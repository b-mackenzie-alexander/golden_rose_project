# ruff: noqa: E501
"""Separately reviewed current facts; original finalization remains immutable."""

import importlib.util
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "0009a_canonical_reviews"
down_revision = "0009_canonical_corrections"
branch_labels = None
depends_on = None
TABLES = ("canonical_review_heads", "canonical_output_reviews", "canonical_output_review_payloads")
FUNCTIONS = (
    "canonical_current_facts(uuid)",
    "guard_canonical_review_identity()",
    "guard_canonical_review()",
)


def execute(sql):
    op.execute(sa.text(sql))


def previous():
    spec = importlib.util.spec_from_file_location(
        "canonical_correction_prior", Path(__file__).with_name("0009_canonical_corrections.py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Missing predecessor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def upgrade():
    execute("""
    CREATE TABLE canonical_review_heads (
      canonical_output_review_id uuid PRIMARY KEY, intake_id uuid NOT NULL UNIQUE REFERENCES intake_finalizations,
      version integer NOT NULL CHECK(version>=0), latest_review_id uuid,
      updated_by uuid, updated_at timestamptz,
      CHECK(canonical_output_review_id=intake_id),
      CHECK((version=0 AND latest_review_id IS NULL AND updated_by IS NULL AND updated_at IS NULL)
        OR (version>0 AND latest_review_id IS NOT NULL AND updated_by IS NOT NULL AND updated_at IS NOT NULL))
    );
    CREATE TABLE canonical_output_reviews (
      review_id uuid PRIMARY KEY, intake_id uuid NOT NULL REFERENCES canonical_review_heads(intake_id),
      original_review_id uuid NOT NULL REFERENCES intake_reviews(review_id),
      command_id uuid NOT NULL UNIQUE REFERENCES command_receipts DEFERRABLE INITIALLY DEFERRED,
      event_id uuid NOT NULL UNIQUE REFERENCES audit_events(audit_event_id) DEFERRABLE INITIALLY DEFERRED,
      result_version integer NOT NULL CHECK(result_version>=1), actor_id uuid NOT NULL,
      occurred_at timestamptz NOT NULL, dependencies jsonb NOT NULL CHECK(jsonb_typeof(dependencies)='object'),
      UNIQUE(intake_id,result_version), UNIQUE(intake_id,review_id)
    );
    ALTER TABLE canonical_review_heads ADD FOREIGN KEY(intake_id,latest_review_id)
      REFERENCES canonical_output_reviews(intake_id,review_id) DEFERRABLE INITIALLY DEFERRED;
    CREATE TABLE canonical_output_review_payloads (
      review_id uuid PRIMARY KEY REFERENCES canonical_output_reviews DEFERRABLE INITIALLY DEFERRED,
      reviewed_content jsonb NOT NULL CHECK(jsonb_typeof(reviewed_content)='object'),
      note varchar(512) CHECK(note IS NULL OR btrim(note)<>''),
      CHECK(octet_length(reviewed_content::text)<=65536)
    );
    ALTER TABLE entity_authorities ADD COLUMN canonical_output_review_id uuid UNIQUE
      REFERENCES canonical_review_heads DEFERRABLE INITIALLY DEFERRED;
    """)
    prior = previous()
    for table, name, column in (
        ("entity_authorities", "ck_entity_authorities_entity_type", "entity_type"),
        ("audit_events", "ck_audit_events_entity_type", "entity_type"),
        ("command_receipts", "ck_command_receipts_entity_type", "result_entity_type"),
    ):
        prior.extend_check(table, name, f"{column}='canonical_output_review'")
    prior.extend_check(
        "command_receipts",
        "ck_command_receipts_command_type",
        "command_type='review_canonical_outputs'",
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
        prior.extend_check(
            table,
            name,
            f"command_type='review_canonical_outputs' AND {prefix}entity_type='canonical_output_review' AND {prefix}event_type='canonical_output_review.reviewed' AND {version}>=1",
        )
    for name, column in (("event_type", "event_type"), ("schema_name", "event_schema_name")):
        prior.extend_check(
            "audit_events",
            f"ck_audit_events_{name}",
            f"{column}='canonical_output_review.reviewed'",
        )
    constraints = {
        x["name"]: x["sqltext"]
        for x in sa.inspect(op.get_bind()).get_check_constraints("entity_authorities")
    }
    name = "ck_entity_authorities_exactly_one_concrete_id"
    old = constraints[name]
    columns = [
        c["name"]
        for c in sa.inspect(op.get_bind()).get_columns("entity_authorities")
        if c["name"].endswith("_id")
        and c["name"] not in ("entity_id", "canonical_output_review_id")
    ]
    op.drop_constraint(name, "entity_authorities", type_="check")
    op.create_check_constraint(
        name,
        "entity_authorities",
        f"(({old}) AND canonical_output_review_id IS NULL) OR (entity_type='canonical_output_review' AND canonical_output_review_id=entity_id AND canonical_output_review_id IS NOT NULL AND "
        + " AND ".join(f"{c} IS NULL" for c in columns)
        + ")",
    )
    execute(CURRENT_FACTS)
    execute(GUARDS)
    execute(
        "CREATE TRIGGER guard_canonical_review_identity BEFORE INSERT OR UPDATE ON canonical_review_heads FOR EACH ROW EXECUTE FUNCTION guard_canonical_review_identity()"
    )
    for table, events in (
        ("canonical_review_heads", "UPDATE"),
        ("canonical_output_reviews", "INSERT"),
        ("canonical_output_review_payloads", "INSERT"),
        ("command_receipts", "INSERT"),
    ):
        execute(
            f"CREATE CONSTRAINT TRIGGER guard_canonical_review AFTER {events} ON {table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION guard_canonical_review()"
        )
    for table in TABLES:
        operations = (
            "DELETE OR TRUNCATE"
            if table == "canonical_review_heads"
            else "UPDATE OR DELETE OR TRUNCATE"
        )
        execute(
            f"CREATE TRIGGER deny_mutation_{table} BEFORE {operations} ON {table} FOR EACH STATEMENT EXECUTE FUNCTION deny_mutation_on_append_only_tables()"
        )
        execute(f"ALTER TABLE {table} OWNER TO golden_rose_schema_owner")
        execute(f"REVOKE ALL ON {table} FROM PUBLIC,golden_rose_runtime,golden_rose_migrator")
        execute(f"GRANT SELECT,INSERT ON {table} TO golden_rose_runtime")
    execute(
        "GRANT UPDATE(version,latest_review_id,updated_by,updated_at) ON canonical_review_heads TO golden_rose_runtime"
    )
    for signature in FUNCTIONS:
        execute(f"ALTER FUNCTION {signature} OWNER TO golden_rose_schema_owner")
        execute(
            f"REVOKE ALL ON FUNCTION {signature} FROM PUBLIC,golden_rose_runtime,golden_rose_migrator"
        )
    execute("GRANT EXECUTE ON FUNCTION canonical_current_facts(uuid) TO golden_rose_runtime")


CURRENT_FACTS = """
CREATE FUNCTION canonical_current_facts(target uuid) RETURNS jsonb LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE f intake_finalizations%ROWTYPE; records jsonb:='{}'; outputs jsonb; k text;
  r jsonb; label text; body jsonb; addresses jsonb; address jsonb; source text;
BEGIN
 SELECT * INTO f FROM intake_finalizations WHERE intake_id=target;
 IF f.intake_id IS NULL THEN RAISE EXCEPTION 'missing finalization' USING ERRCODE='23514'; END IF;
 outputs:=jsonb_build_object('kind',f.kind);
 FOREACH k IN ARRAY ARRAY['employer','employer_address','employer_contact','employer_contact_details',
   'staffing_request','worker','worker_contact','worker_preferences','worker_residence','worksite'] LOOP
   label:=CASE k WHEN 'employer_contact' THEN 'contact' WHEN 'employer_contact_details' THEN 'contact_details'
     WHEN 'employer_address' THEN 'business_address' WHEN 'staffing_request' THEN 'request'
     WHEN 'worker_contact' THEN 'contact' WHEN 'worker_preferences' THEN 'preferences'
     WHEN 'worker_residence' THEN 'residence' ELSE k END;
   IF to_jsonb(f)->>(k||'_id') IS NULL THEN CONTINUE; END IF;
   r:=intake_canonical_record(k,(to_jsonb(f)->>(k||'_id'))::uuid);
   records:=records||jsonb_build_object(k,r);
   outputs:=outputs||jsonb_build_object(label,jsonb_build_object('id',to_jsonb(f)->(k||'_id'),
      'version',r->'version','disposition',to_jsonb(f)->(k||'_disposition')));
 END LOOP;
 IF f.kind='worker' THEN
   body:=jsonb_build_object('full_name',records->'worker'->'full_name','phone',records->'worker_contact'->'phone',
     'interests',records->'worker_preferences'->'interests','availability',records->'worker_preferences'->'availability');
 ELSE
   IF f.employer_address_id IS NULL THEN outputs:=outputs||'{"business_address": null}'::jsonb; END IF;
   body:=jsonb_build_object('employer_type',records->'employer'->'employer_type','display_name',records->'employer'->'display_name',
     'representative_name',records->'employer_contact_details'->'representative_name','phone',records->'employer_contact_details'->'phone',
     'role_title',records->'staffing_request'->'role_title','duties_summary',records->'staffing_request'->'duties_summary',
     'worker_count',records->'staffing_request'->'worker_count','schedule',records->'staffing_request'->'schedule','offer',records->'staffing_request'->'offer');
 END IF;
 addresses:='{}';
 FOREACH label IN ARRAY CASE WHEN f.kind='worker' THEN ARRAY['worker_residence'] ELSE ARRAY['party_address','worksite_address'] END LOOP
   source:=CASE label WHEN 'worker_residence' THEN 'worker_residence' WHEN 'worksite_address' THEN 'worksite'
     ELSE CASE WHEN records->'employer'->>'employer_type'='household' THEN 'employer_contact_details' ELSE 'employer_address' END END;
   r:=COALESCE(records->source,'{}'::jsonb);
   address:=jsonb_strip_nulls(jsonb_build_object('line1',r->'line1','line2',r->'line2','locality',r->'locality',
     'region',r->'region','postal_code',r->'postal_code','country',r->'country'));
   addresses:=addresses||jsonb_build_object(label,address);
 END LOOP;
 RETURN jsonb_build_object('dependencies',outputs,'snapshot',jsonb_build_object('kind',f.kind,'content',body,'addresses',addresses));
END $$;
"""

GUARDS = """
CREATE FUNCTION guard_canonical_review_identity() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF TG_OP='INSERT' THEN
   IF NEW.version<>0 THEN RAISE EXCEPTION 'initial review head must be empty' USING ERRCODE='23514'; END IF;
 ELSIF (NEW.intake_id,NEW.canonical_output_review_id) IS DISTINCT FROM (OLD.intake_id,OLD.canonical_output_review_id)
   OR NEW.version<>OLD.version+1 THEN RAISE EXCEPTION 'invalid review head advancement' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
CREATE FUNCTION guard_canonical_review() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE r canonical_output_reviews%ROWTYPE; h canonical_review_heads%ROWTYPE;
  p canonical_output_review_payloads%ROWTYPE; f intake_finalizations%ROWTYPE; facts jsonb;
BEGIN
 IF TG_TABLE_NAME='command_receipts' THEN
   IF NEW.command_type<>'review_canonical_outputs' THEN RETURN NULL; END IF;
   SELECT * INTO r FROM canonical_output_reviews WHERE command_id=NEW.command_id;
 ELSIF TG_TABLE_NAME='canonical_review_heads' THEN
   SELECT * INTO r FROM canonical_output_reviews WHERE review_id=NEW.latest_review_id;
 ELSE SELECT * INTO r FROM canonical_output_reviews WHERE review_id=NEW.review_id; END IF;
 SELECT * INTO h FROM canonical_review_heads WHERE intake_id=r.intake_id FOR UPDATE;
 SELECT * INTO p FROM canonical_output_review_payloads WHERE review_id=r.review_id;
 SELECT * INTO f FROM intake_finalizations WHERE intake_id=r.intake_id;
 facts:=canonical_current_facts(r.intake_id);
 IF f.kind='worker' THEN
   IF NOT canonical_details_complete('availability',facts->'snapshot'->'content'->'availability') THEN
     RAISE EXCEPTION 'incomplete current availability' USING ERRCODE='23514'; END IF;
   PERFORM 1 FROM work_interests w JOIN worker_interest_selections s USING(interest_id)
     WHERE s.worker_preferences_id=f.worker_preferences_id ORDER BY w.interest_id FOR UPDATE OF w;
   IF EXISTS(SELECT 1 FROM worker_interest_selections s JOIN work_interests w USING(interest_id)
      WHERE s.worker_preferences_id=f.worker_preferences_id AND (NOT w.active OR w.version<>s.catalog_version)) THEN
     RAISE EXCEPTION 'current interests require review' USING ERRCODE='23514'; END IF;
 END IF;
 IF f.kind='employer' AND NOT canonical_details_complete('schedule',facts->'snapshot'->'content'->'schedule') THEN
   RAISE EXCEPTION 'incomplete current schedule' USING ERRCODE='23514'; END IF;
 IF EXISTS(SELECT 1 FROM jsonb_each(facts->'snapshot'->'addresses') a WHERE
    NULLIF(btrim(a.value->>'line1'),'') IS NULL OR NULLIF(btrim(a.value->>'locality'),'') IS NULL OR
    NULLIF(btrim(a.value->>'country'),'') IS NULL OR (a.value->>'country'='US' AND
    (NULLIF(btrim(a.value->>'region'),'') IS NULL OR NULLIF(btrim(a.value->>'postal_code'),'') IS NULL))) THEN
   RAISE EXCEPTION 'incomplete current address' USING ERRCODE='23514'; END IF;
 IF r.review_id IS NULL OR h.intake_id IS NULL OR p.review_id IS NULL OR f.intake_id IS NULL OR
   NOT EXISTS(SELECT 1 FROM command_receipts c WHERE c.command_id=r.command_id
     AND c.created_at=r.occurred_at AND c.actor_id=r.actor_id
     AND c.result_entity_id=r.intake_id AND c.result_record_version=r.result_version) OR
   r.original_review_id<>f.review_id OR h.latest_review_id<>r.review_id OR h.version<>r.result_version OR
   (h.updated_by,h.updated_at) IS DISTINCT FROM (r.actor_id,r.occurred_at) OR
   r.dependencies IS DISTINCT FROM facts->'dependencies' OR p.reviewed_content IS DISTINCT FROM facts->'snapshot' OR
   NOT EXISTS(SELECT 1 FROM canonical_review_heads WHERE intake_id=r.intake_id AND xmin::text=pg_current_xact_id()::text) OR
   NOT EXISTS(SELECT 1 FROM canonical_output_reviews WHERE review_id=r.review_id AND xmin::text=pg_current_xact_id()::text) OR
   NOT EXISTS(SELECT 1 FROM canonical_output_review_payloads WHERE review_id=r.review_id AND xmin::text=pg_current_xact_id()::text) OR
   NOT EXISTS(SELECT 1 FROM command_results x JOIN audit_events a ON a.command_id=x.command_id AND a.entity_type=x.entity_type AND a.entity_id=x.entity_id
     WHERE x.command_id=r.command_id AND x.command_type='review_canonical_outputs' AND x.entity_type='canonical_output_review'
       AND x.entity_id=r.intake_id AND x.result_version=r.result_version AND x.actor_id=r.actor_id
       AND a.audit_event_id=r.event_id AND a.occurred_at=r.occurred_at AND a.xmin::text=pg_current_xact_id()::text
       AND a.changed_fields='{"field_names":["current_review"],"approved_values":{}}'::jsonb) THEN
   RAISE EXCEPTION 'invalid canonical review evidence' USING ERRCODE='23514'; END IF;
 RETURN NULL;
END $$;
"""


def downgrade():
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS(SELECT 1 FROM canonical_output_reviews) OR EXISTS(SELECT 1 FROM canonical_review_heads)"
        )
    ):
        raise RuntimeError("canonical review data blocks downgrade before DDL")
    execute("SET CONSTRAINTS ALL IMMEDIATE")
    for table in (*TABLES, "command_receipts"):
        execute(f"DROP TRIGGER IF EXISTS guard_canonical_review ON {table}")
    execute("DROP TRIGGER guard_canonical_review_identity ON canonical_review_heads")
    for signature in reversed(FUNCTIONS):
        execute(f"DROP FUNCTION {signature}")
    correction = previous()
    correction.restore_authority_shapes(True)
    op.drop_column("entity_authorities", "canonical_output_review_id")
    execute(
        "ALTER TABLE canonical_review_heads DROP CONSTRAINT canonical_review_heads_intake_id_latest_review_id_fkey"
    )
    for table in reversed(TABLES):
        op.drop_table(table)
