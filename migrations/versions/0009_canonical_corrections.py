# ruff: noqa: E501
"""Canonical current-fact corrections with protected atomic section evidence."""

import importlib.util
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "0009_canonical_corrections"
down_revision = "0008c_intake_link_authority"
branch_labels = None
depends_on = None

ADDRESS = ("line1", "line2", "locality", "region", "postal_code", "country")
SPECS = {
    "correct_worker": ("worker", "workers", ("full_name",)),
    "correct_worker_contact": ("worker_contact", "worker_contacts", ("phone",)),
    "correct_worker_residence": ("worker_residence", "worker_residences", ADDRESS),
    "correct_worker_preferences": (
        "worker_preferences",
        "worker_preferences",
        ("interests", "availability"),
    ),
    "correct_contact_details": (
        "employer_contact_details",
        "employer_contact_details",
        ("representative_name", "phone"),
    ),
    "correct_contact_address": ("employer_contact_details", "employer_contact_details", ADDRESS),
    "correct_employer_address": ("employer_address", "employer_addresses", ADDRESS),
    "correct_worksite_address": ("worksite", "worksites", ADDRESS),
    "correct_staffing_request": (
        "staffing_request",
        "staffing_requests",
        ("role_title", "duties_summary", "worker_count", "schedule", "offer"),
    ),
}
TABLES = {kind: table for kind, table, _ in SPECS.values()}
NEW_TABLES = ("canonical_corrections", "canonical_correction_payloads")


def execute(sql: str) -> None:
    op.execute(sa.text(sql))


def prior():
    spec = importlib.util.spec_from_file_location(
        "correction_prior", Path(__file__).with_name("0008c_intake_link_authority.py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Missing applied predecessor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extend_check(table: str, name: str, arm: str) -> None:
    constraints = {
        row["name"]: row["sqltext"]
        for row in sa.inspect(op.get_bind()).get_check_constraints(table)
    }
    old = constraints[name]
    op.drop_constraint(name, table, type_="check")
    op.create_check_constraint(name, table, f"({old}) OR ({arm})")


def section_function() -> str:
    branches = []
    for command, (_, _, fields) in SPECS.items():
        values = ",".join(f"'{field}',data->'{field}'" for field in fields)
        expression = f"jsonb_strip_nulls(jsonb_build_object({values}))"
        if fields == ADDRESS:
            expression = f"jsonb_build_object('address',{expression})"
        branches.append(f"WHEN '{command}' THEN RETURN {expression};")
    return (
        """CREATE FUNCTION canonical_correction_section(command text,data jsonb)
      RETURNS jsonb LANGUAGE plpgsql IMMUTABLE SET search_path=pg_catalog,public,pg_temp AS $$
      BEGIN CASE command """
        + "\n".join(branches)
        + """
      ELSE RAISE EXCEPTION 'invalid correction command' USING ERRCODE='23514'; END CASE; END $$;"""
    )


def correction_shapes() -> None:
    kinds = ",".join(f"'{kind}'" for kind in TABLES)
    extend_check(
        "command_receipts", "ck_command_receipts_entity_type", f"result_entity_type IN ({kinds})"
    )
    commands = ",".join(f"'{c}'" for c in SPECS)
    events = ",".join(f"'{k}.corrected'" for k in TABLES)
    extend_check(
        "command_receipts", "ck_command_receipts_command_type", f"command_type IN ({commands})"
    )
    for table, name, prefix, version in (
        (
            "command_receipts",
            "ck_command_receipts_result_authority_shape",
            "result_",
            "result_record_version",
        ),
        ("command_results", "ck_command_results_authority_shape", "", "result_version"),
    ):
        arm = " OR ".join(
            f"(command_type='{c}' AND {prefix}entity_type='{k}' AND {prefix}event_type='{k}.corrected' AND {version}>=2)"
            for c, (k, _, _) in SPECS.items()
        )
        extend_check(table, name, arm)
    for name, column in (("event_type", "event_type"), ("schema_name", "event_schema_name")):
        extend_check("audit_events", f"ck_audit_events_{name}", f"{column} IN ({events})")


def restore_authority_shapes(include_corrections: bool) -> None:
    """Restore predecessor checks directly, never installing a narrower intermediate check."""
    linked = prior()
    employer = linked.predecessor()
    worker = employer.predecessor()
    base = worker.predecessor()
    primary = (
        base.BASE_SHAPE
        + base.EXTRA_SHAPE
        + """ OR
      (command_type='finalize_intake' AND result_entity_type='intake'
        AND result_event_type='intake.finalized' AND result_record_version>=3)
      OR (command_type='link_intake' AND result_entity_type='intake'
          AND result_event_type='intake.linked' AND result_record_version>=2)"""
    )
    commands = (
        base.BASE_COMMANDS
        + ",'review_intake','follow_up_intake','create_work_interest','revise_work_interest','finalize_intake','link_intake'"
    )
    events = (
        base.BASE_EVENTS
        + ",'intake.reviewed','intake.follow_up_recorded','work_interest.created','work_interest.revised','intake.finalized',"
        + ",".join(f"'{k}.created'" for k in (*worker.KINDS, *employer.TABLES))
        + ",'intake.linked'"
    )
    result = (
        primary.replace("result_entity_type", "entity_type")
        .replace("result_event_type", "event_type")
        .replace("result_record_version", "result_version")
    )
    result += (
        " OR (command_type='finalize_intake' AND result_version=1 AND ("
        + " OR ".join(f"(entity_type='{k}' AND event_type='{k}.created')" for k in linked.TABLES)
        + "))"
    )
    if include_corrections:
        commands += "," + ",".join(f"'{c}'" for c in SPECS)
        events += "," + ",".join(f"'{k}.corrected'" for k in TABLES)
        primary += " OR " + " OR ".join(
            f"(command_type='{c}' AND result_entity_type='{k}' AND result_event_type='{k}.corrected' AND result_record_version>=2)"
            for c, (k, _, _) in SPECS.items()
        )
        result += " OR " + " OR ".join(
            f"(command_type='{c}' AND entity_type='{k}' AND event_type='{k}.corrected' AND result_version>=2)"
            for c, (k, _, _) in SPECS.items()
        )
    worker.check(
        "command_receipts", "ck_command_receipts_command_type", f"command_type IN ({commands})"
    )
    worker.check("command_receipts", "ck_command_receipts_result_authority_shape", primary)
    worker.check("command_results", "ck_command_results_authority_shape", result)
    receipt_kinds = ["employer", "employer_contact", "intake", "work_interest"] + (
        list(TABLES) if include_corrections else []
    )
    worker.check(
        "command_receipts",
        "ck_command_receipts_entity_type",
        "result_entity_type IN (" + ",".join(f"'{k}'" for k in receipt_kinds) + ")",
    )
    for column, name in (("event_type", "event_type"), ("event_schema_name", "schema_name")):
        worker.check("audit_events", f"ck_audit_events_{name}", f"{column} IN ({events})")
    concrete = (
        "employer",
        "employer_contact",
        "intake",
        "work_interest",
        *worker.KINDS,
        *employer.TABLES,
    )
    types = ",".join(f"'{k}'" for k in concrete)
    worker.check("audit_events", "ck_audit_events_entity_type", f"entity_type IN ({types})")
    worker.check(
        "entity_authorities", "ck_entity_authorities_entity_type", f"entity_type IN ({types})"
    )
    worker.check(
        "entity_authorities",
        "ck_entity_authorities_exactly_one_concrete_id",
        " OR ".join(
            f"(entity_type='{kind}' AND {kind}_id IS NOT NULL AND {kind}_id=entity_id AND "
            + " AND ".join(f"{other}_id IS NULL" for other in concrete if other != kind)
            + ")"
            for kind in concrete
        ),
    )


def upgrade() -> None:
    execute(
        "LOCK TABLE "
        + ",".join(
            (
                *TABLES.values(),
                "worker_interest_selections",
                "command_receipts",
                "command_results",
                "audit_events",
            )
        )
        + " IN SHARE ROW EXCLUSIVE MODE"
    )
    execute("""
    CREATE TABLE canonical_corrections (
      event_id uuid PRIMARY KEY REFERENCES audit_events(audit_event_id) DEFERRABLE INITIALLY DEFERRED,
      command_id uuid NOT NULL UNIQUE REFERENCES command_receipts DEFERRABLE INITIALLY DEFERRED,
      command_type varchar(64) NOT NULL,
      entity_type varchar(64) NOT NULL, entity_id uuid NOT NULL,
      previous_version integer NOT NULL CHECK(previous_version>=1),
      result_version integer NOT NULL CHECK(result_version=previous_version+1),
      actor_id uuid NOT NULL, occurred_at timestamptz NOT NULL, corrects_event_id uuid,
      FOREIGN KEY(entity_type,entity_id) REFERENCES entity_authorities(entity_type,entity_id),
      UNIQUE(event_id,entity_type,entity_id), UNIQUE(entity_type,entity_id,result_version),
      FOREIGN KEY(corrects_event_id,entity_type,entity_id)
        REFERENCES canonical_corrections(event_id,entity_type,entity_id),
      CHECK(corrects_event_id IS DISTINCT FROM event_id)
    );
    CREATE TABLE canonical_correction_payloads (
      event_id uuid PRIMARY KEY REFERENCES canonical_corrections DEFERRABLE INITIALLY DEFERRED,
      reason_text varchar(512) NOT NULL CHECK(btrim(reason_text)<>''),
      before jsonb NOT NULL CHECK(jsonb_typeof(before)='object'),
      after jsonb NOT NULL CHECK(jsonb_typeof(after)='object'),
      CHECK(before IS DISTINCT FROM after),
      CHECK(octet_length(before::text)<=65536 AND octet_length(after::text)<=65536)
    );
    """)
    arms = " OR ".join(
        f"(command_type='{command}' AND entity_type='{kind}')"
        for command, (kind, _, _) in SPECS.items()
    )
    op.create_check_constraint("ck_canonical_correction_command", "canonical_corrections", arms)
    correction_shapes()
    for kind, table in TABLES.items():
        constraints = sa.inspect(op.get_bind()).get_check_constraints(table)
        for constraint in constraints:
            expression = constraint["sqltext"]
            if "created_at = updated_at" in expression and "created_by = updated_by" in expression:
                op.drop_constraint(constraint["name"], table, type_="check")
            elif expression == "version = 1":
                op.drop_constraint(constraint["name"], table, type_="check")
                op.create_check_constraint(constraint["name"], table, "version>=1")
        execute(f"DROP TRIGGER deny_mutation_{table} ON {table}")
        execute(
            f"CREATE TRIGGER deny_mutation_{table} BEFORE DELETE OR TRUNCATE ON {table} FOR EACH STATEMENT EXECUTE FUNCTION deny_mutation_on_append_only_tables()"
        )
        fields = sorted({f for k, _, fs in SPECS.values() if k == kind for f in fs})
        execute(
            f"GRANT UPDATE({','.join((*fields, 'version', 'updated_at', 'updated_by'))}) ON {table} TO golden_rose_runtime"
        )
    op.alter_column("worker_contacts", "phone", type_=sa.String(40), existing_type=sa.String(32))
    predecessor = prior()
    canonical = predecessor.canonical_function().replace(
        "CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1
    )
    # Lock every canonical row; callers traverse a fixed entity order.
    canonical = canonical.replace(" INTO result FROM ", " INTO result FROM ")
    for kind in predecessor.TABLES:
        if kind == "employer_contact":
            continue
        canonical = canonical.replace(
            f"WHERE {kind}_id=target;", f"WHERE {kind}_id=target FOR UPDATE;"
        )
    execute(canonical)
    snapshot = predecessor.SNAPSHOT.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1)
    snapshot = snapshot.replace(
        "facts->'employer_contact'->'full_name'",
        "facts->'employer_contact_details'->'representative_name'",
    )
    execute(snapshot)
    execute(section_function())
    execute(GUARDS)
    for kind, table in TABLES.items():
        execute(
            f"CREATE TRIGGER guard_canonical_identity BEFORE INSERT OR UPDATE ON {table} FOR EACH ROW EXECUTE FUNCTION guard_canonical_identity('{kind}')"
        )
        execute(
            f"CREATE CONSTRAINT TRIGGER guard_canonical_correction AFTER UPDATE ON {table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION guard_canonical_correction('{kind}')"
        )
    for table in (*NEW_TABLES, "command_receipts"):
        execute(
            f"CREATE CONSTRAINT TRIGGER guard_correction_evidence AFTER INSERT ON {table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION guard_correction_evidence()"
        )
    for table in NEW_TABLES:
        execute(
            f"CREATE TRIGGER deny_mutation_{table} BEFORE UPDATE OR DELETE OR TRUNCATE ON {table} FOR EACH STATEMENT EXECUTE FUNCTION deny_mutation_on_append_only_tables()"
        )
        execute(f"ALTER TABLE {table} OWNER TO golden_rose_schema_owner")
        execute(f"REVOKE ALL ON {table} FROM PUBLIC,golden_rose_runtime,golden_rose_migrator")
        execute(f"GRANT SELECT,INSERT ON {table} TO golden_rose_runtime")
    # Selection replacement receives a separate exact correction guard.
    execute("DROP TRIGGER deny_mutation_worker_interest_selections ON worker_interest_selections")
    execute(
        "CREATE TRIGGER deny_mutation_worker_interest_selections BEFORE UPDATE OR TRUNCATE ON worker_interest_selections FOR EACH STATEMENT EXECUTE FUNCTION deny_mutation_on_append_only_tables()"
    )
    execute("GRANT DELETE ON worker_interest_selections TO golden_rose_runtime")
    execute("DROP TRIGGER guard_worker_output ON worker_interest_selections")
    execute(SELECTION_GUARD)
    execute(
        "CREATE CONSTRAINT TRIGGER guard_worker_selection AFTER INSERT OR DELETE ON worker_interest_selections DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION guard_worker_selection()"
    )
    for signature in (
        "canonical_details_complete(text,jsonb)",
        "canonical_correction_section(text,jsonb)",
        "guard_canonical_identity()",
        "guard_canonical_correction()",
        "guard_correction_evidence()",
        "guard_worker_selection()",
    ):
        execute(f"ALTER FUNCTION {signature} OWNER TO golden_rose_schema_owner")
        execute(
            f"REVOKE ALL ON FUNCTION {signature} FROM PUBLIC,golden_rose_runtime,golden_rose_migrator"
        )
    execute(
        "GRANT EXECUTE ON FUNCTION canonical_correction_section(text,jsonb), canonical_details_complete(text,jsonb) TO golden_rose_runtime"
    )


GUARDS = """
CREATE FUNCTION canonical_details_complete(kind text, value jsonb) RETURNS boolean LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE item jsonb; other jsonb; start_min int; end_min int; starts int[]:='{}'; ends int[]:='{}';
  idx int; shift int; tz text; first_at timestamptz; last_at timestamptz;
BEGIN
 IF value IS NULL OR jsonb_typeof(value)<>'object' THEN RETURN false; END IF;
 tz:=value->>'time_zone';
 IF tz IS NOT NULL AND NOT EXISTS(SELECT 1 FROM pg_timezone_names WHERE name=tz) THEN RETURN false; END IF;
 IF kind='availability' THEN
   IF value->>'mode'='flexible' THEN RETURN NOT value ? 'ranges'; END IF;
   IF value->>'mode' IS DISTINCT FROM 'weekly' OR tz IS NULL OR jsonb_typeof(value->'ranges') IS DISTINCT FROM 'array'
      OR jsonb_array_length(value->'ranges') NOT BETWEEN 1 AND 28 THEN RETURN false; END IF;
   FOR item IN SELECT * FROM jsonb_array_elements(value->'ranges') LOOP
     IF jsonb_typeof(item)<>'object' OR NOT item ?& ARRAY['weekday','start_local','end_local','end_day_offset'] OR
       jsonb_typeof(item->'weekday')<>'number' OR (item->>'weekday') !~ '^[1-7]$' OR
       jsonb_typeof(item->'end_day_offset')<>'number' OR (item->>'end_day_offset') !~ '^[01]$' OR
       jsonb_typeof(item->'start_local') IS DISTINCT FROM 'string' OR jsonb_typeof(item->'end_local') IS DISTINCT FROM 'string' OR
       (item->>'start_local') !~ '^([01][0-9]|2[0-3]):[0-5][0-9]$' OR
       (item->>'end_local') !~ '^([01][0-9]|2[0-3]):[0-5][0-9]$' THEN RETURN false; END IF;
     start_min:=((item->>'weekday')::int-1)*1440 + extract(epoch FROM (item->>'start_local')::time)::int/60;
     end_min:=((item->>'weekday')::int-1+(item->>'end_day_offset')::int)*1440 + extract(epoch FROM (item->>'end_local')::time)::int/60;
     IF end_min-start_min NOT BETWEEN 1 AND 1440 THEN RETURN false; END IF;
     FOR idx IN 1..COALESCE(array_length(starts,1),0) LOOP
       FOREACH shift IN ARRAY ARRAY[-10080,0,10080] LOOP
         IF start_min < ends[idx]+shift AND starts[idx]+shift < end_min THEN RETURN false; END IF;
       END LOOP;
     END LOOP;
     starts:=array_append(starts,start_min); ends:=array_append(ends,end_min);
   END LOOP;
   RETURN true;
 ELSIF kind='schedule' THEN
   IF value->>'mode'='to_be_discussed' THEN
     RETURN NOT value ?| ARRAY['requested_start_date','starts_at','ends_at','time_zone']; END IF;
   IF value->>'mode' IS DISTINCT FROM 'specified' THEN RETURN false; END IF;
   IF value ? 'requested_start_date' THEN
     IF value ?| ARRAY['starts_at','ends_at','time_zone'] OR
       (value->>'requested_start_date') IS NULL OR (value->>'requested_start_date') !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN RETURN false; END IF;
     RETURN (value->>'requested_start_date')::date IS NOT NULL;
   END IF;
   IF tz IS NULL OR NOT value ?& ARRAY['starts_at','ends_at'] THEN RETURN false; END IF;
   FOREACH item IN ARRAY ARRAY[value->'starts_at',value->'ends_at'] LOOP
     IF jsonb_typeof(item)<>'string' OR (item#>>'{}') !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}([.][0-9]{1,6})?(Z|[+-]([01][0-9]|2[0-3]):[0-5][0-9])$' THEN RETURN false; END IF;
     IF ((item#>>'{}')::timestamptz AT TIME ZONE tz) IS DISTINCT FROM (item#>>'{}')::timestamp THEN RETURN false; END IF;
   END LOOP;
   first_at:=(value->>'starts_at')::timestamptz; last_at:=(value->>'ends_at')::timestamptz;
   RETURN last_at>first_at;
 END IF;
 RETURN false;
EXCEPTION WHEN invalid_text_representation OR datetime_field_overflow OR invalid_datetime_format OR invalid_parameter_value THEN
 RETURN false;
END $$;
CREATE FUNCTION guard_canonical_identity() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE allowed text[]; oldj jsonb; newj jsonb;
BEGIN
 IF TG_OP='INSERT' THEN
   IF NEW.version<>1 OR NEW.created_by<>NEW.updated_by OR NEW.created_at<>NEW.updated_at THEN
     RAISE EXCEPTION 'invalid canonical initial attribution' USING ERRCODE='23514'; END IF;
   RETURN NEW;
 END IF;
 oldj:=to_jsonb(OLD); newj:=to_jsonb(NEW);
 allowed:=CASE TG_ARGV[0]
   WHEN 'worker' THEN ARRAY['full_name'] WHEN 'worker_contact' THEN ARRAY['phone']
   WHEN 'worker_preferences' THEN ARRAY['interests','availability']
   WHEN 'employer_contact_details' THEN ARRAY['representative_name','phone','line1','line2','locality','region','postal_code','country']
   WHEN 'staffing_request' THEN ARRAY['role_title','duties_summary','worker_count','schedule','offer']
   ELSE ARRAY['line1','line2','locality','region','postal_code','country'] END;
 IF NEW.version<>OLD.version+1 OR NEW.updated_at<OLD.updated_at OR
   (newj-(allowed||ARRAY['version','updated_at','updated_by'])) IS DISTINCT FROM
   (oldj-(allowed||ARRAY['version','updated_at','updated_by'])) THEN
   RAISE EXCEPTION 'immutable canonical identity or invalid version' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;

CREATE FUNCTION guard_canonical_correction() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE c canonical_corrections%ROWTYPE; p canonical_correction_payloads%ROWTYPE;
  target uuid; fields text[]; before_section jsonb; after_section jsonb;
BEGIN
 target:=(to_jsonb(NEW)->>(TG_ARGV[0]||'_id'))::uuid;
 SELECT * INTO c FROM canonical_corrections WHERE entity_type=TG_ARGV[0]
   AND entity_id=target AND result_version=NEW.version;
 SELECT * INTO p FROM canonical_correction_payloads WHERE event_id=c.event_id;
 before_section:=canonical_correction_section(c.command_type,to_jsonb(OLD));
 after_section:=canonical_correction_section(c.command_type,to_jsonb(NEW));
 SELECT array_agg(key) INTO fields FROM jsonb_object_keys(
   CASE WHEN after_section ? 'address' THEN after_section->'address' ELSE after_section END) AS key;
 fields:=COALESCE(fields,ARRAY[]::text[]);
 IF after_section ? 'address' THEN fields:=ARRAY['line1','line2','locality','region','postal_code','country']; END IF;
 IF c.event_id IS NULL OR p.event_id IS NULL OR
   (c.previous_version,c.result_version,c.actor_id,c.occurred_at) IS DISTINCT FROM
   (OLD.version,NEW.version,NEW.updated_by,NEW.updated_at) OR
   p.before IS DISTINCT FROM before_section OR p.after IS DISTINCT FROM after_section OR
   (to_jsonb(NEW)-(fields||ARRAY['version','updated_by','updated_at'])) IS DISTINCT FROM
   (to_jsonb(OLD)-(fields||ARRAY['version','updated_by','updated_at'])) OR
   NOT EXISTS(SELECT 1 FROM canonical_corrections WHERE event_id=c.event_id
     AND xmin::text=pg_current_xact_id()::text) OR
   NOT EXISTS(SELECT 1 FROM canonical_correction_payloads WHERE event_id=c.event_id
     AND xmin::text=pg_current_xact_id()::text) THEN
   RAISE EXCEPTION 'missing exact canonical correction evidence' USING ERRCODE='23514';
 END IF;
 IF c.command_type='correct_contact_address' AND NOT EXISTS(
   SELECT 1 FROM employers WHERE employer_id=(to_jsonb(NEW)->>'employer_id')::uuid AND employer_type='household') THEN
   RAISE EXCEPTION 'contact address requires household' USING ERRCODE='23514'; END IF;
 IF c.command_type='correct_contact_address' AND (
   (to_jsonb(NEW)->>'line1') IS NULL OR btrim((to_jsonb(NEW)->>'line1'))='' OR (to_jsonb(NEW)->>'locality') IS NULL OR btrim((to_jsonb(NEW)->>'locality'))=''
   OR (to_jsonb(NEW)->>'country') IS NULL OR ((to_jsonb(NEW)->>'country')='US' AND ((to_jsonb(NEW)->>'region') IS NULL OR btrim((to_jsonb(NEW)->>'region'))=''
      OR (to_jsonb(NEW)->>'postal_code') IS NULL OR btrim((to_jsonb(NEW)->>'postal_code'))=''))) THEN
   RAISE EXCEPTION 'complete household address required' USING ERRCODE='23514'; END IF;
 IF c.command_type='correct_staffing_request' AND NOT canonical_details_complete('schedule',to_jsonb(NEW)->'schedule') THEN
   RAISE EXCEPTION 'complete corrected schedule required' USING ERRCODE='23514'; END IF;
 IF c.command_type='correct_worker_preferences' THEN
   IF NOT canonical_details_complete('availability',to_jsonb(NEW)->'availability') THEN
     RAISE EXCEPTION 'complete corrected availability required' USING ERRCODE='23514'; END IF;
   PERFORM 1 FROM work_interests w JOIN worker_interest_selections s USING(interest_id)
     WHERE s.worker_preferences_id=target ORDER BY w.interest_id FOR UPDATE OF w;
   IF (SELECT COALESCE(jsonb_agg(jsonb_build_object('interest_id',interest_id,'catalog_version',catalog_version) ORDER BY interest_id),'[]')
       FROM worker_interest_selections WHERE worker_preferences_id=target) IS DISTINCT FROM
      (SELECT COALESCE(jsonb_agg(value ORDER BY value->>'interest_id'),'[]') FROM jsonb_array_elements(COALESCE(to_jsonb(NEW)->'interests'->'selections','[]'))) OR
      EXISTS(SELECT 1 FROM worker_interest_selections s JOIN work_interests w USING(interest_id)
       WHERE s.worker_preferences_id=target AND (NOT w.active OR w.version<>s.catalog_version)) THEN
     RAISE EXCEPTION 'invalid corrected preference selections' USING ERRCODE='23514'; END IF;
 END IF;
 RETURN NULL;
END $$;

CREATE FUNCTION guard_correction_evidence() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE c canonical_corrections%ROWTYPE; p canonical_correction_payloads%ROWTYPE;
  a audit_events%ROWTYPE; r command_results%ROWTYPE; receipt command_receipts%ROWTYPE;
  target jsonb; tab text; fields jsonb;
BEGIN
 IF TG_TABLE_NAME='command_receipts' THEN
   IF NEW.command_type NOT LIKE 'correct_%' THEN RETURN NULL; END IF;
   SELECT * INTO c FROM canonical_corrections WHERE command_id=NEW.command_id;
 ELSE SELECT * INTO c FROM canonical_corrections WHERE event_id=NEW.event_id; END IF;
 SELECT * INTO p FROM canonical_correction_payloads WHERE event_id=c.event_id;
 SELECT * INTO a FROM audit_events WHERE audit_event_id=c.event_id;
 SELECT * INTO r FROM command_results WHERE command_id=c.command_id;
 SELECT * INTO receipt FROM command_receipts WHERE command_id=c.command_id;
 tab:=CASE c.entity_type WHEN 'worker' THEN 'workers' WHEN 'worker_contact' THEN 'worker_contacts'
   WHEN 'worker_residence' THEN 'worker_residences' WHEN 'worker_preferences' THEN 'worker_preferences'
   WHEN 'employer_contact_details' THEN 'employer_contact_details' WHEN 'employer_address' THEN 'employer_addresses'
   WHEN 'worksite' THEN 'worksites' WHEN 'staffing_request' THEN 'staffing_requests' END;
 IF tab IS NULL THEN RAISE EXCEPTION 'missing correction target' USING ERRCODE='23514'; END IF;
 EXECUTE format('SELECT to_jsonb(t)||jsonb_build_object(''_written_here'',t.xmin::text=pg_current_xact_id()::text) FROM %I t WHERE %I=$1',tab,c.entity_type||'_id') INTO target USING c.entity_id;
 SELECT jsonb_agg(key ORDER BY key) INTO fields FROM jsonb_object_keys(p.after) AS key;
 IF c.event_id IS NULL OR p.event_id IS NULL OR a.audit_event_id IS NULL OR r.command_id IS NULL OR receipt.command_id IS NULL OR target IS NULL OR
   (r.entity_type,r.entity_id,r.result_version,r.actor_id,r.command_type,r.event_type) IS DISTINCT FROM
   (c.entity_type,c.entity_id,c.result_version,c.actor_id,c.command_type,c.entity_type||'.corrected') OR
   (receipt.result_entity_type,receipt.result_entity_id,receipt.result_record_version,receipt.actor_id,receipt.command_type,receipt.created_at) IS DISTINCT FROM
   (c.entity_type,c.entity_id,c.result_version,c.actor_id,c.command_type,c.occurred_at) OR
   (a.command_id,a.entity_type,a.entity_id,a.prior_record_version,a.new_record_version,a.actor_id,a.occurred_at,a.event_type) IS DISTINCT FROM
   (c.command_id,c.entity_type,c.entity_id,c.previous_version,c.result_version,c.actor_id,c.occurred_at,c.entity_type||'.corrected') OR
   (target->>'version')::integer<>c.result_version OR (target->>'updated_by')::uuid<>c.actor_id OR
   (target->>'updated_at')::timestamptz<>c.occurred_at OR target->'_written_here'<>'true'::jsonb OR
   canonical_correction_section(c.command_type,target) IS DISTINCT FROM p.after OR
   NOT EXISTS(SELECT 1 FROM audit_events WHERE audit_event_id=c.event_id AND xmin::text=pg_current_xact_id()::text) OR
   a.changed_fields IS DISTINCT FROM jsonb_build_object('field_names',fields,'approved_values','{}'::jsonb) OR
   (c.corrects_event_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM canonical_corrections prior WHERE
     prior.event_id=c.corrects_event_id AND prior.result_version<=c.previous_version)) THEN
   RAISE EXCEPTION 'invalid atomic correction group' USING ERRCODE='23514'; END IF;
 RETURN NULL;
END $$;
"""

SELECTION_GUARD = """
CREATE FUNCTION guard_worker_selection() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE target uuid; prefs worker_preferences%ROWTYPE; selections jsonb;
BEGIN
 target:=CASE WHEN TG_OP='DELETE' THEN OLD.worker_preferences_id ELSE NEW.worker_preferences_id END;
 SELECT * INTO prefs FROM worker_preferences WHERE worker_preferences_id=target FOR UPDATE;
 SELECT COALESCE(jsonb_agg(jsonb_build_object('interest_id',interest_id,'catalog_version',catalog_version) ORDER BY interest_id),'[]')
 INTO selections FROM worker_interest_selections WHERE worker_preferences_id=target;
 IF selections IS DISTINCT FROM (SELECT COALESCE(jsonb_agg(value ORDER BY value->>'interest_id'),'[]')
   FROM jsonb_array_elements(COALESCE(prefs.interests->'selections','[]'))) OR
   EXISTS(SELECT 1 FROM worker_interest_selections s JOIN work_interests w USING(interest_id)
     WHERE s.worker_preferences_id=target AND (NOT w.active OR w.version<>s.catalog_version)) OR
   NOT EXISTS(SELECT 1 FROM worker_preferences WHERE worker_preferences_id=target AND xmin::text=pg_current_xact_id()::text) OR
   (prefs.version>1 AND NOT EXISTS(SELECT 1 FROM canonical_corrections c WHERE
     c.entity_type='worker_preferences' AND c.entity_id=target AND c.result_version=prefs.version
     AND c.command_type='correct_worker_preferences' AND c.xmin::text=pg_current_xact_id()::text)) OR
   (prefs.version=1 AND (TG_OP='DELETE' OR NOT EXISTS(SELECT 1 FROM command_results r
     JOIN audit_events a ON a.command_id=r.command_id AND a.entity_type=r.entity_type AND a.entity_id=r.entity_id
     WHERE r.entity_type='worker_preferences' AND r.entity_id=target AND r.result_version=1
       AND r.command_type='finalize_intake' AND a.xmin::text=pg_current_xact_id()::text))) THEN
   RAISE EXCEPTION 'invalid atomic preference selections' USING ERRCODE='23514'; END IF;
 RETURN NULL;
END $$;
"""


def downgrade() -> None:
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS(SELECT 1 FROM canonical_corrections) OR EXISTS(SELECT 1 FROM canonical_correction_payloads)"
        )
    ):
        raise RuntimeError("canonical correction data blocks downgrade before DDL")
    execute("SET CONSTRAINTS ALL IMMEDIATE")
    predecessor = prior()
    for table in (*NEW_TABLES, "command_receipts"):
        execute(f"DROP TRIGGER guard_correction_evidence ON {table}")
    for kind, table in TABLES.items():
        execute(f"DROP TRIGGER guard_canonical_identity ON {table}")
        execute(f"DROP TRIGGER guard_canonical_correction ON {table}")
        execute(f"DROP TRIGGER deny_mutation_{table} ON {table}")
        execute(
            f"CREATE TRIGGER deny_mutation_{table} BEFORE UPDATE OR DELETE OR TRUNCATE ON {table} FOR EACH STATEMENT EXECUTE FUNCTION deny_mutation_on_append_only_tables()"
        )
        fields = sorted({f for k, _, fs in SPECS.values() if k == kind for f in fs})
        execute(
            f"REVOKE UPDATE({','.join((*fields, 'version', 'updated_at', 'updated_by'))}) ON {table} FROM golden_rose_runtime"
        )
        op.drop_constraint(f"{table}_version_check", table, type_="check")
        op.create_check_constraint(f"{table}_version_check", table, "version=1")
        op.create_check_constraint(
            f"{table}_check", table, "created_at=updated_at AND created_by=updated_by"
        )
    execute("DROP TRIGGER guard_worker_selection ON worker_interest_selections")
    execute("DROP TRIGGER deny_mutation_worker_interest_selections ON worker_interest_selections")
    execute(
        "CREATE TRIGGER deny_mutation_worker_interest_selections BEFORE UPDATE OR DELETE OR TRUNCATE ON worker_interest_selections FOR EACH STATEMENT EXECUTE FUNCTION deny_mutation_on_append_only_tables()"
    )
    execute(
        "CREATE CONSTRAINT TRIGGER guard_worker_output AFTER INSERT ON worker_interest_selections DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION guard_worker_output('worker_preferences')"
    )
    execute("REVOKE DELETE ON worker_interest_selections FROM golden_rose_runtime")
    for signature in (
        "guard_worker_selection()",
        "guard_correction_evidence()",
        "guard_canonical_correction()",
        "guard_canonical_identity()",
        "canonical_correction_section(text,jsonb)",
        "canonical_details_complete(text,jsonb)",
    ):
        execute(f"DROP FUNCTION {signature}")
    for table in reversed(NEW_TABLES):
        op.drop_table(table)
    restore_authority_shapes(False)
    execute(
        predecessor.canonical_function().replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1)
    )
    execute(predecessor.SNAPSHOT.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1))
    op.alter_column("worker_contacts", "phone", type_=sa.String(32), existing_type=sa.String(40))
