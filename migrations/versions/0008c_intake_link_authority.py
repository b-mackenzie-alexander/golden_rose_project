"""Admit atomic links, effective review snapshots and created/reused outputs."""

import importlib.util
from pathlib import Path
from types import ModuleType

import sqlalchemy as sa
from alembic import op

revision = "0008c_intake_link_authority"
down_revision = "0008b_intake_link_storage"
branch_labels = None
depends_on = None

TABLES = {
    "worker": "workers",
    "worker_contact": "worker_contacts",
    "worker_residence": "worker_residences",
    "worker_preferences": "worker_preferences",
    "employer": "employers",
    "employer_contact": "employer_contacts",
    "employer_contact_details": "employer_contact_details",
    "employer_address": "employer_addresses",
    "worksite": "worksites",
    "staffing_request": "staffing_requests",
}
PARENTS = ("worker", "employer")
CHILDREN = tuple(k for k in TABLES if k not in (*PARENTS, "staffing_request"))
LINK_COLUMNS = [*(f"{k}_id" for k in PARENTS)] + [
    f"{k}_{suffix}" for k in CHILDREN for suffix in ("id", "version")
]
PARENT_COLUMNS = "worker_id,worker_version,employer_id,employer_version"
FUNCTIONS = (
    "intake_canonical_record(text,uuid)",
    "intake_link_refs(uuid)",
    "intake_effective_snapshot(uuid)",
    "guard_intake_links()",
    "guard_intake_link_event()",
    "guard_intake_link_once()",
)


def predecessor(filename: str = "0008a_employer_finalization.py") -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "link_authority_prior", Path(__file__).with_name(filename)
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Required link authority predecessor unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def execute(sql: str) -> None:
    op.execute(sa.text(sql))


def replace_once(sql: str, old: str, new: str) -> str:
    """Fail closed if an inherited function no longer has the expected definition."""
    if sql.count(old) != 1:
        raise RuntimeError("Applied predecessor definition changed")
    return sql.replace(old, new, 1)


def shapes(active: bool) -> None:
    employer = predecessor()
    worker = employer.predecessor()
    prior = worker.predecessor()
    primary = (
        prior.BASE_SHAPE
        + prior.EXTRA_SHAPE
        + """ OR
      (command_type='finalize_intake' AND result_entity_type='intake'
        AND result_event_type='intake.finalized' AND result_record_version>=3)"""
    )
    commands = prior.BASE_COMMANDS + (
        ",'review_intake','follow_up_intake','create_work_interest','revise_work_interest',"
        "'finalize_intake'"
    )
    events = (
        prior.BASE_EVENTS
        + (
            ",'intake.reviewed','intake.follow_up_recorded','work_interest.created',"
            "'work_interest.revised','intake.finalized',"
        )
        + ",".join(f"'{k}.created'" for k in (*worker.KINDS, *employer.TABLES))
    )
    if active:
        commands += ",'link_intake'"
        events += ",'intake.linked'"
        primary += """ OR (command_type='link_intake' AND result_entity_type='intake'
          AND result_event_type='intake.linked' AND result_record_version>=2)"""
    result = (
        primary.replace("result_entity_type", "entity_type")
        .replace("result_event_type", "event_type")
        .replace("result_record_version", "result_version")
    )
    result += (
        " OR (command_type='finalize_intake' AND result_version=1 AND ("
        + " OR ".join(f"(entity_type='{k}' AND event_type='{k}.created')" for k in TABLES)
        + "))"
    )
    worker.check(
        "command_receipts", "ck_command_receipts_command_type", f"command_type IN ({commands})"
    )
    worker.check("command_receipts", "ck_command_receipts_result_authority_shape", primary)
    worker.check("command_results", "ck_command_results_authority_shape", result)
    for column, name in (("event_type", "event_type"), ("event_schema_name", "schema_name")):
        worker.check("audit_events", f"ck_audit_events_{name}", f"{column} IN ({events})")


def canonical_function() -> str:
    branches = []
    for kind, table in TABLES.items():
        # Identifiers come only from this migration's fixed table map, never input.
        branches.append(
            f"WHEN '{kind}' THEN SELECT to_jsonb(t)||jsonb_build_object('_written_here',"  # nosec B608
            f"t.xmin::text=pg_current_xact_id()::text) INTO result FROM {table} t "
            f"WHERE {kind}_id=target" + (" FOR UPDATE;" if kind == "employer" else ";")
        )
    return (
        """
    CREATE FUNCTION intake_canonical_record(kind text,target uuid) RETURNS jsonb
    LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
    DECLARE result jsonb;
    BEGIN CASE kind
    """
        + "\n".join(branches)
        + """
    ELSE RAISE EXCEPTION 'invalid canonical kind' USING ERRCODE='23514'; END CASE;
    IF result IS NULL THEN
      RAISE EXCEPTION 'missing canonical dependency' USING ERRCODE='23514'; END IF;
    RETURN result;
    END $$;
    """
    )


LINK_REFS = """
CREATE FUNCTION intake_link_refs(target uuid) RETURNS jsonb LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE parent jsonb; children jsonb; result jsonb:='{}'; kind text;
BEGIN
 SELECT to_jsonb(i) INTO parent FROM intakes i WHERE intake_id=target;
 SELECT to_jsonb(l) INTO children FROM intake_links l WHERE intake_id=target;
 FOREACH kind IN ARRAY ARRAY['worker','employer','worker_contact','worker_residence',
   'worker_preferences','employer_contact','employer_contact_details','employer_address','worksite']
 LOOP
   IF kind IN ('worker','employer') THEN
     IF parent->> (kind||'_id') IS NOT NULL THEN
       result:=result||jsonb_build_object(kind,jsonb_build_object(
         'id',parent->(kind||'_id'),'version',parent->(kind||'_version')));
     END IF;
   ELSIF children->>(kind||'_id') IS NOT NULL THEN
     result:=result||jsonb_build_object(kind,jsonb_build_object(
       'id',children->(kind||'_id'),'version',children->(kind||'_version')));
   END IF;
 END LOOP;
 RETURN result;
END $$;
"""

SNAPSHOT = """
CREATE FUNCTION intake_effective_snapshot(target uuid) RETURNS jsonb LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE i intakes%ROWTYPE; refs jsonb; facts jsonb:='{}'; body jsonb; addresses jsonb;
  k text; record jsonb; parent jsonb; address jsonb; section text;
BEGIN
 SELECT * INTO i FROM intakes WHERE intake_id=target;
 refs:=intake_link_refs(target);
 body:=i.content;
 SELECT COALESCE(jsonb_object_agg(a.section,jsonb_strip_nulls(to_jsonb(a)-'intake_id'-'section'))
   FILTER(WHERE jsonb_strip_nulls(to_jsonb(a)-'intake_id'-'section')<>'{}'::jsonb),'{}'::jsonb)
   INTO addresses FROM intake_addresses a WHERE intake_id=target;
 IF refs='{}'::jsonb THEN
   RETURN jsonb_build_object('kind',i.kind,'content',body,'addresses',addresses);
 END IF;
 IF NOT refs ? i.kind THEN RAISE EXCEPTION 'missing link parent' USING ERRCODE='23514'; END IF;
 -- The mutable parent is locked before children, matching the application protocol.
 parent:=intake_canonical_record(i.kind,(refs->i.kind->>'id')::uuid);
 IF i.kind='employer' AND parent->>'lifecycle_status'<>'draft' THEN
   RAISE EXCEPTION 'invalid linked employer lifecycle' USING ERRCODE='23514';
 END IF;
 FOR k IN SELECT jsonb_object_keys(refs) ORDER BY 1 LOOP
   record:=CASE WHEN k=i.kind THEN parent
     ELSE intake_canonical_record(k,(refs->k->>'id')::uuid) END;
   IF (record->>'version')::integer IS DISTINCT FROM (refs->k->>'version')::integer
     OR (k<>i.kind AND record->>(i.kind||'_id') IS DISTINCT FROM refs->i.kind->>'id')
     OR (k='employer_contact_details' AND record->>'employer_contact_id'
       IS DISTINCT FROM refs->'employer_contact'->>'id') THEN
     RAISE EXCEPTION 'stale or wrong-parent dependency' USING ERRCODE='23514';
   END IF;
   facts:=facts||jsonb_build_object(k,record);
 END LOOP;
 IF i.kind='worker' THEN
   IF facts->'worker_preferences'->'self_reported' IS DISTINCT FROM 'true'::jsonb THEN
     RAISE EXCEPTION 'invalid linked preferences' USING ERRCODE='23514';
   END IF;
   body:=jsonb_build_object('full_name',parent->'full_name',
     'phone',facts->'worker_contact'->'phone',
     'interests',facts->'worker_preferences'->'interests',
     'availability',facts->'worker_preferences'->'availability');
 ELSE
   body:=body||jsonb_build_object('employer_type',parent->'employer_type',
     'display_name',parent->'display_name');
   IF refs ? 'employer_contact' THEN
     body:=body||jsonb_build_object('representative_name',facts->'employer_contact'->'full_name',
       'phone',facts->'employer_contact_details'->'phone');
   END IF;
   IF refs ? 'employer_address' AND (parent->>'employer_type'<>'business'
     OR facts->'employer_address'->>'purpose'<>'business') THEN
     RAISE EXCEPTION 'wrong linked address purpose' USING ERRCODE='23514';
   END IF;
 END IF;
 FOREACH k IN ARRAY ARRAY['worker_residence','employer_contact_details',
   'employer_address','worksite']
 LOOP
   IF NOT refs ? k OR (k='employer_contact_details' AND parent->>'employer_type'<>'household') THEN
     CONTINUE;
   END IF;
   section:=CASE k WHEN 'worker_residence' THEN k WHEN 'worksite' THEN 'worksite_address'
     ELSE 'party_address' END;
   record:=facts->k;
   address:=jsonb_strip_nulls(jsonb_build_object('line1',record->'line1','line2',record->'line2',
     'locality',record->'locality','region',record->'region',
     'postal_code',record->'postal_code','country',record->'country'));
   addresses:=addresses||jsonb_build_object(section,address);
 END LOOP;
 RETURN jsonb_build_object('kind',i.kind,'content',body,'addresses',addresses);
END $$;
"""

LINK_AUTHORITY = """
CREATE FUNCTION guard_intake_links() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE i intakes%ROWTYPE; l intake_links%ROWTYPE; r command_results%ROWTYPE;
  changed boolean; refs jsonb; k text; record jsonb;
BEGIN
 SELECT * INTO i FROM intakes WHERE intake_id=NEW.intake_id;
 SELECT * INTO l FROM intake_links WHERE intake_id=NEW.intake_id;
 SELECT * INTO r FROM command_results WHERE entity_type='intake' AND entity_id=i.intake_id
   AND result_version=i.version;
 IF TG_TABLE_NAME='intakes' THEN
   IF TG_OP='INSERT' THEN
     IF NEW.worker_id IS NOT NULL OR NEW.employer_id IS NOT NULL OR l.intake_id IS NOT NULL THEN
       RAISE EXCEPTION 'links require a separate command' USING ERRCODE='23514';
     END IF;
     RETURN NULL;
   END IF;
   changed:=(NEW.worker_id,NEW.worker_version,NEW.employer_id,NEW.employer_version)
     IS DISTINCT FROM (OLD.worker_id,OLD.worker_version,OLD.employer_id,OLD.employer_version);
   IF r.command_type IS DISTINCT FROM 'link_intake' THEN
     IF changed THEN RAISE EXCEPTION 'link changed outside command' USING ERRCODE='23514'; END IF;
     RETURN NULL;
   END IF;
   IF OLD.lifecycle_status<>'draft' OR NEW.lifecycle_status<>'draft'
     OR NEW.content IS DISTINCT FROM OLD.content OR NEW.content_version<>OLD.content_version+1
     OR NEW.version<>OLD.version+1 THEN
     RAISE EXCEPTION 'invalid link version delta' USING ERRCODE='23514';
   END IF;
 ELSE
   IF to_jsonb(NEW) IS DISTINCT FROM to_jsonb(l) THEN
     RAISE EXCEPTION 'multiple link replacements in one transaction' USING ERRCODE='23514';
   END IF;
   IF TG_OP='UPDATE' THEN
     IF NEW.intake_id<>OLD.intake_id OR NEW IS NOT DISTINCT FROM OLD THEN
       RAISE EXCEPTION 'invalid link replacement' USING ERRCODE='23514';
     END IF;
   ELSIF i.worker_id IS NULL AND i.employer_id IS NULL THEN
     RAISE EXCEPTION 'empty initial links' USING ERRCODE='23514';
   END IF;
 END IF;
 IF r.command_type IS DISTINCT FROM 'link_intake' OR i.lifecycle_status<>'draft'
   OR l.intake_id IS NULL
   OR (l.worker_id,l.employer_id) IS DISTINCT FROM (i.worker_id,i.employer_id)
   OR NOT EXISTS(SELECT 1 FROM intakes WHERE intake_id=i.intake_id
     AND xmin::text=pg_current_xact_id()::text)
   OR (NOT COALESCE(TG_TABLE_NAME='intakes' AND changed,false) AND NOT EXISTS(
     SELECT 1 FROM intake_links WHERE intake_id=i.intake_id
       AND xmin::text=pg_current_xact_id()::text))
   OR NOT EXISTS(SELECT 1 FROM audit_events a WHERE a.command_id=r.command_id
     AND a.entity_type='intake' AND a.entity_id=i.intake_id AND a.event_type='intake.linked'
     AND a.actor_id=i.updated_by AND a.occurred_at=i.updated_at AND a.new_record_version=i.version
     AND a.changed_fields='{"field_names":["links"],"approved_values":{}}'::jsonb
     AND a.xmin::text=pg_current_xact_id()::text) THEN
   RAISE EXCEPTION 'missing atomic link authority' USING ERRCODE='23514';
 END IF;
 -- Linking checks identity/version/parentage, not completeness of canonical facts.
 refs:=intake_link_refs(i.intake_id);
 IF refs ? 'employer' THEN
   record:=intake_canonical_record('employer',(refs->'employer'->>'id')::uuid);
   IF record->>'lifecycle_status'<>'draft' OR (refs ? 'employer_address'
     AND record->>'employer_type'<>'business') THEN
     RAISE EXCEPTION 'invalid linked employer' USING ERRCODE='23514';
   END IF;
 END IF;
 FOR k IN SELECT jsonb_object_keys(refs) ORDER BY 1 LOOP
   record:=intake_canonical_record(k,(refs->k->>'id')::uuid);
   IF (record->>'version')::integer IS DISTINCT FROM (refs->k->>'version')::integer
     OR (k<>i.kind AND record->>(i.kind||'_id') IS DISTINCT FROM refs->i.kind->>'id')
     OR (k='employer_contact_details' AND record->>'employer_contact_id'
       IS DISTINCT FROM refs->'employer_contact'->>'id') THEN
     RAISE EXCEPTION 'invalid link reference' USING ERRCODE='23514';
   END IF;
 END LOOP;
 RETURN NULL;
END $$;
"""

LINK_EVENT_AUTHORITY = """
CREATE FUNCTION guard_intake_link_event() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF NEW.event_type='intake.linked' AND NOT EXISTS(
   SELECT 1 FROM intakes i WHERE i.intake_id=NEW.entity_id
     AND NEW.entity_type='intake' AND i.version=NEW.new_record_version
     AND i.updated_by=NEW.actor_id AND i.updated_at=NEW.occurred_at
     AND i.lifecycle_status='draft' AND i.xmin::text=pg_current_xact_id()::text
 ) THEN
   RAISE EXCEPTION 'link event without atomic intake update' USING ERRCODE='23514';
 END IF;
 RETURN NULL;
END $$;
"""

LINK_ONCE_AUTHORITY = """
CREATE FUNCTION guard_intake_link_once() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 -- Paired with queued-row validation: early constraint flushing cannot admit a second write.
 IF EXISTS(SELECT 1 FROM intake_links WHERE intake_id=OLD.intake_id
   AND xmin::text=pg_current_xact_id()::text) THEN
   RAISE EXCEPTION 'multiple link replacements in one transaction' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
"""


def intake_authority() -> str:
    sql = predecessor().predecessor().INTAKE_AUTHORITY
    sql = replace_once(sql, "AND NEW.kind='worker'", "AND NEW.kind IN ('worker','employer')")
    return replace_once(
        sql,
        "r.command_type IN ('revise_intake','revise_intake_address')",
        "r.command_type IN ('revise_intake','revise_intake_address','link_intake')",
    )


def workflow_authority() -> str:
    sql = predecessor().predecessor().predecessor().WORKFLOW_FUNCTION
    start = sql.index("   SELECT jsonb_build_object('kind',parent.kind")
    end = sql.index("   IF rev.review_id IS NULL", start)
    sql = sql[:start] + "   expected:=intake_effective_snapshot(parent.intake_id);\n" + sql[end:]
    sql = replace_once(
        sql,
        "OR payload.reviewed_content IS DISTINCT FROM expected",
        "OR payload.dependency_refs IS DISTINCT FROM intake_link_refs(parent.intake_id)\n"
        "     OR payload.reviewed_content IS DISTINCT FROM expected",
    )
    return replace_once(sql, "CREATE FUNCTION", "CREATE OR REPLACE FUNCTION")


FINALIZATION_AUTHORITY = """
CREATE OR REPLACE FUNCTION guard_finalization_results() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE c command_receipts%ROWTYPE; f intake_finalizations%ROWTYPE; i intakes%ROWTYPE;
  r intake_reviews%ROWTYPE; payload intake_review_payloads%ROWTYPE; n integer; expected integer:=1;
  data jsonb; refs jsonb; reused jsonb:='{}'; k text; record jsonb; parent jsonb;
  output_id uuid; output_version integer; disposition text; catalog record;
BEGIN
 SELECT * INTO c FROM command_receipts WHERE command_id=NEW.command_id;
 SELECT count(*) INTO n FROM command_results WHERE command_id=NEW.command_id;
 IF c.command_id IS NULL THEN RAISE EXCEPTION 'missing receipt' USING ERRCODE='23514'; END IF;
 IF c.command_type<>'finalize_intake' THEN
   IF n<>1 THEN RAISE EXCEPTION 'unexpected command results' USING ERRCODE='23514'; END IF;
   RETURN NULL;
 END IF;
 SELECT * INTO f FROM intake_finalizations WHERE command_id=c.command_id;
 SELECT * INTO i FROM intakes WHERE intake_id=f.intake_id;
 SELECT * INTO r FROM intake_reviews WHERE intake_id=f.intake_id
   ORDER BY result_version DESC LIMIT 1;
 SELECT * INTO payload FROM intake_review_payloads WHERE review_id=f.review_id;
 refs:=intake_link_refs(f.intake_id);
 IF f.intake_id IS NULL OR i.intake_id IS NULL OR r.review_id IS NULL OR payload.review_id IS NULL
   OR (c.result_entity_id,c.result_record_version,c.actor_id,c.created_at) IS DISTINCT FROM
     (f.intake_id,f.result_version,f.actor_id,f.occurred_at)
   OR (i.kind,i.lifecycle_status,i.version,i.content_version,i.updated_by,i.updated_at)
     IS DISTINCT FROM
     (f.kind,'finalized'::varchar,f.result_version,f.content_version,f.actor_id,f.occurred_at)
   OR (r.review_id,r.outcome,r.reviewed_content_version) IS DISTINCT FROM
     (f.review_id,'intake_reviewed'::varchar,f.content_version)
   OR payload.dependency_refs IS DISTINCT FROM refs
   OR payload.reviewed_content IS DISTINCT FROM intake_effective_snapshot(f.intake_id)
   OR NOT EXISTS(SELECT 1 FROM intakes WHERE intake_id=f.intake_id
     AND xmin::text=pg_current_xact_id()::text)
   OR NOT EXISTS(SELECT 1 FROM intake_finalizations WHERE intake_id=f.intake_id
     AND xmin::text=pg_current_xact_id()::text)
   OR EXISTS(SELECT 1 FROM audit_events a WHERE a.command_id=c.command_id AND
     (a.actor_id<>f.actor_id OR a.occurred_at<>f.occurred_at
       OR a.xmin::text<>pg_current_xact_id()::text)) THEN
   RAISE EXCEPTION 'invalid finalization review authority' USING ERRCODE='23514';
 END IF;
 data:=to_jsonb(f);
 parent:=intake_canonical_record(f.kind,(data->>(f.kind||'_id'))::uuid);
 FOREACH k IN ARRAY ARRAY['worker','worker_contact','worker_residence','worker_preferences',
   'employer','employer_contact','employer_contact_details','employer_address','worksite','staffing_request']
 LOOP
   output_id:=(data->>(k||'_id'))::uuid;
   IF output_id IS NULL THEN CONTINUE; END IF;
   output_version:=(data->>(k||'_version'))::integer;
   disposition:=data->>(k||'_disposition');
   record:=intake_canonical_record(k,output_id);
   IF (record->>'version')::integer IS DISTINCT FROM output_version
     OR (k<>f.kind AND record->>(f.kind||'_id') IS DISTINCT FROM data->>(f.kind||'_id'))
     OR (k='employer_contact_details' AND record->>'employer_contact_id'
       IS DISTINCT FROM data->>'employer_contact_id') THEN
     RAISE EXCEPTION 'wrong output reference or parent' USING ERRCODE='23514';
   END IF;
   IF disposition='reused' THEN
     reused:=reused||jsonb_build_object(k,jsonb_build_object('id',output_id,'version',output_version));
     IF EXISTS(SELECT 1 FROM command_results WHERE command_id=c.command_id AND entity_type=k) THEN
       RAISE EXCEPTION 'reuse cannot create authority' USING ERRCODE='23514';
     END IF;
   ELSE
     expected:=expected+1;
     IF NOT EXISTS(SELECT 1 FROM command_results WHERE command_id=c.command_id
       AND entity_type=k AND entity_id=output_id AND result_version=1 AND event_type=k||'.created')
       OR (record->>'created_by')::uuid IS DISTINCT FROM f.actor_id
       OR record->'_written_here' IS DISTINCT FROM 'true'::jsonb
       OR (record->>'created_at')::timestamptz IS DISTINCT FROM f.occurred_at THEN
       RAISE EXCEPTION 'missing created output authority' USING ERRCODE='23514';
     END IF;
   END IF;
 END LOOP;
 IF reused IS DISTINCT FROM refs OR n<>expected THEN
   RAISE EXCEPTION 'wrong finalization result cardinality or reuse' USING ERRCODE='23514';
 END IF;
 IF f.kind='employer' THEN
   record:=intake_canonical_record('staffing_request',f.staffing_request_id);
   IF (record->>'employer_contact_id',record->>'worksite_id',record->>'employer_address_id',
       record->>'request_type') IS DISTINCT FROM
     (f.employer_contact_id::text,f.worksite_id::text,f.employer_address_id::text,
       CASE WHEN parent->>'employer_type'='household' THEN 'household' ELSE 'general_labor' END)
     OR parent->>'lifecycle_status'<>'draft' THEN
     RAISE EXCEPTION 'wrong staffing request parents or type' USING ERRCODE='23514';
   END IF;
   IF parent->>'employer_type'='household' THEN
     record:=intake_canonical_record('employer_contact_details',f.employer_contact_details_id);
     IF NOT COALESCE(btrim(record->>'line1')<>'' AND btrim(record->>'locality')<>''
       AND record->>'country' ~ '^[A-Z]{2}$' AND (record->>'country'<>'US' OR
         (btrim(record->>'region')<>'' AND btrim(record->>'postal_code')<>'')),false) THEN
       RAISE EXCEPTION 'incomplete household output address' USING ERRCODE='23514';
     END IF;
   END IF;
 ELSE
   FOR catalog IN SELECT w.version,w.active,s.catalog_version FROM work_interests w
     JOIN worker_interest_selections s USING(interest_id)
     WHERE s.worker_preferences_id=f.worker_preferences_id ORDER BY w.interest_id FOR UPDATE OF w
   LOOP
     IF NOT catalog.active OR catalog.version<>catalog.catalog_version THEN
       RAISE EXCEPTION 'stale finalization catalog' USING ERRCODE='23514';
     END IF;
   END LOOP;
 END IF;
 RETURN NULL;
END $$;
"""


def output_authority(kind: str) -> str:
    prior = predecessor() if kind == "employer" else predecessor().predecessor()
    sql = replace_once(prior.OUTPUT_AUTHORITY, "CREATE FUNCTION", "CREATE OR REPLACE FUNCTION")
    sql = replace_once(
        sql,
        "(to_jsonb(intake_finalizations)->>(v_kind||'_id'))::uuid=target;",
        "(to_jsonb(intake_finalizations)->>(v_kind||'_id'))::uuid=target\n"
        "    AND to_jsonb(intake_finalizations)->>(v_kind||'_disposition')='created';",
    )
    sql = replace_once(
        sql,
        "SELECT content INTO candidate FROM intakes WHERE intake_id=f.intake_id;",
        "SELECT reviewed_content->'content' INTO candidate FROM intake_review_payloads "
        "WHERE review_id=f.review_id;",
    )
    if kind == "worker":
        sql = replace_once(
            sql,
            "SELECT jsonb_strip_nulls(to_jsonb(a)-'intake_id'-'section') INTO address\n"
            "     FROM intake_addresses a WHERE intake_id=f.intake_id "
            "AND section='worker_residence';",
            "SELECT reviewed_content->'addresses'->'worker_residence' INTO address\n"
            "     FROM intake_review_payloads WHERE review_id=f.review_id;",
        )
    else:
        sql = replace_once(
            sql,
            "SELECT jsonb_strip_nulls(to_jsonb(a)-'intake_id'-'section') INTO expected_address\n"
            "      FROM intake_addresses a WHERE intake_id=f.intake_id\n"
            "      AND section=CASE WHEN v_kind='worksite' "
            "THEN 'worksite_address' ELSE 'party_address' END;",
            "SELECT reviewed_content->'addresses'->\n"
            "        (CASE WHEN v_kind='worksite' THEN 'worksite_address' "
            "ELSE 'party_address' END)\n"
            "        INTO expected_address FROM intake_review_payloads "
            "WHERE review_id=f.review_id;",
        )
    return sql


def parent_shape(cleared: bool) -> str:
    worker = tuple(k for k in CHILDREN if k.startswith("worker_"))
    employer = tuple(k for k in CHILDREN if not k.startswith("worker_"))
    shape = (
        "(worker_id IS NOT NULL AND employer_id IS NULL AND "
        + " AND ".join(
            [*(f"{k}_id IS NOT NULL" for k in worker), *(f"{k}_id IS NULL" for k in employer)]
        )
        + ") OR (employer_id IS NOT NULL AND worker_id IS NULL AND "
        + " AND ".join(f"{k}_id IS NULL" for k in worker)
        + ")"
    )
    if cleared:
        shape += " OR (" + " AND ".join(f"{k}_id IS NULL" for k in (*PARENTS, *CHILDREN)) + ")"
    return shape


def output_constraints(active: bool) -> None:
    for k in TABLES:
        if k == "staffing_request":
            continue
        for suffix in ("version", "disposition"):
            op.drop_constraint(
                f"intake_finalizations_{k}_{suffix}_check", "intake_finalizations", type_="check"
            )
        if active:
            op.drop_constraint(
                f"intake_finalizations_{k}_id_key", "intake_finalizations", type_="unique"
            )
            op.create_check_constraint(
                f"intake_finalizations_{k}_version_check",
                "intake_finalizations",
                f"{k}_version>=1 AND ({k}_disposition<>'created' OR {k}_version=1)",
            )
            op.create_check_constraint(
                f"intake_finalizations_{k}_disposition_check",
                "intake_finalizations",
                f"{k}_disposition IN ('created','reused')",
            )
            execute(
                f"CREATE UNIQUE INDEX uq_finalization_created_{k} "
                f"ON intake_finalizations({k}_id) WHERE {k}_disposition='created'"
            )
        else:
            execute(f"DROP INDEX uq_finalization_created_{k}")
            op.create_unique_constraint(
                f"intake_finalizations_{k}_id_key", "intake_finalizations", [f"{k}_id"]
            )
            op.create_check_constraint(
                f"intake_finalizations_{k}_version_check", "intake_finalizations", f"{k}_version=1"
            )
            op.create_check_constraint(
                f"intake_finalizations_{k}_disposition_check",
                "intake_finalizations",
                f"{k}_disposition='created'",
            )


def upgrade() -> None:
    execute(
        "LOCK TABLE intakes,intake_links,intake_reviews,intake_review_payloads,"
        "intake_finalizations,command_receipts,command_results,audit_events "
        "IN SHARE ROW EXCLUSIVE MODE"
    )
    shapes(True)
    output_constraints(True)
    op.create_check_constraint(
        "ck_finalization_reuse_shape",
        "intake_finalizations",
        """
      (kind='worker' AND worker_disposition=worker_contact_disposition
        AND worker_disposition=worker_residence_disposition
        AND worker_disposition=worker_preferences_disposition)
      OR (kind='employer' AND staffing_request_disposition='created'
        AND employer_contact_disposition=employer_contact_details_disposition
        AND (employer_disposition='reused' OR (employer_contact_disposition='created'
          AND worksite_disposition='created'
          AND COALESCE(employer_address_disposition,'created')='created')))
    """,
    )
    execute(canonical_function())
    execute(LINK_REFS)
    execute(SNAPSHOT)
    execute(LINK_AUTHORITY)
    execute(LINK_EVENT_AUTHORITY)
    execute(LINK_ONCE_AUTHORITY)
    execute(intake_authority())
    execute(workflow_authority())
    execute(FINALIZATION_AUTHORITY)
    execute(output_authority("worker"))
    execute(output_authority("employer"))
    for table in ("intakes", "intake_links"):
        execute(
            f"CREATE CONSTRAINT TRIGGER guard_intake_links AFTER INSERT OR UPDATE ON {table} "
            "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION guard_intake_links()"
        )
    execute(
        "CREATE CONSTRAINT TRIGGER guard_intake_link_event AFTER INSERT ON audit_events "
        "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION guard_intake_link_event()"
    )
    execute(
        "CREATE TRIGGER guard_intake_link_once BEFORE UPDATE ON intake_links "
        "FOR EACH ROW EXECUTE FUNCTION guard_intake_link_once()"
    )
    execute("DROP TRIGGER deny_mutation_intake_links ON intake_links")
    execute(
        "CREATE TRIGGER deny_mutation_intake_links BEFORE DELETE OR TRUNCATE ON intake_links "
        "FOR EACH STATEMENT EXECUTE FUNCTION deny_mutation_on_append_only_tables()"
    )
    predecessor().predecessor().check(
        "intake_links", "ck_intake_links_parent_shape", parent_shape(True)
    )
    op.drop_constraint(
        "intake_review_payloads_dependency_refs_check", "intake_review_payloads", type_="check"
    )
    op.create_check_constraint(
        "intake_review_payloads_dependency_refs_check",
        "intake_review_payloads",
        "jsonb_typeof(dependency_refs)='object'",
    )
    for function in FUNCTIONS:
        execute(f"ALTER FUNCTION {function} OWNER TO golden_rose_schema_owner")
        execute(
            f"REVOKE ALL ON FUNCTION {function} "
            "FROM PUBLIC,golden_rose_runtime,golden_rose_migrator"
        )
    for function in FUNCTIONS[:3]:
        execute(f"GRANT EXECUTE ON FUNCTION {function} TO golden_rose_runtime")
    execute(f"GRANT UPDATE({PARENT_COLUMNS}) ON intakes TO golden_rose_runtime")
    execute(f"GRANT UPDATE({','.join(LINK_COLUMNS)}) ON intake_links TO golden_rose_runtime")
    op.drop_constraint("ck_intakes_links_not_available", "intakes", type_="check")
    op.drop_constraint("ck_intake_links_not_available", "intake_links", type_="check")


def downgrade() -> None:
    execute(
        "LOCK TABLE intakes,intake_links,intake_review_payloads,intake_finalizations,"
        "command_receipts,command_results,audit_events IN SHARE ROW EXCLUSIVE MODE"
    )
    populated = (
        op.get_bind()
        .execute(
            sa.text("""SELECT
      EXISTS(SELECT 1 FROM intake_links) OR
      EXISTS(SELECT 1 FROM intakes WHERE worker_id IS NOT NULL OR employer_id IS NOT NULL) OR
      EXISTS(SELECT 1 FROM command_receipts WHERE command_type='link_intake') OR
      EXISTS(SELECT 1 FROM intake_review_payloads WHERE dependency_refs<>'{}'::jsonb) OR
      EXISTS(SELECT 1 FROM intake_finalizations f, jsonb_each(to_jsonb(f)) e
        WHERE e.value='"reused"'::jsonb)
    """)
        )
        .scalar_one()
    )
    if populated:
        raise RuntimeError("link/reuse data blocks downgrade before DDL")
    execute("SET CONSTRAINTS ALL IMMEDIATE")
    op.create_check_constraint("ck_intake_links_not_available", "intake_links", "false")
    op.create_check_constraint(
        "ck_intakes_links_not_available", "intakes", "worker_id IS NULL AND employer_id IS NULL"
    )
    execute(f"REVOKE UPDATE({PARENT_COLUMNS}) ON intakes FROM golden_rose_runtime")
    execute(f"REVOKE UPDATE({','.join(LINK_COLUMNS)}) ON intake_links FROM golden_rose_runtime")
    for table in ("intakes", "intake_links"):
        execute(f"DROP TRIGGER guard_intake_links ON {table}")
    execute("DROP TRIGGER guard_intake_link_event ON audit_events")
    execute("DROP TRIGGER guard_intake_link_once ON intake_links")
    execute("DROP TRIGGER deny_mutation_intake_links ON intake_links")
    execute(
        "CREATE TRIGGER deny_mutation_intake_links "
        "BEFORE UPDATE OR DELETE OR TRUNCATE ON intake_links "
        "FOR EACH STATEMENT EXECUTE FUNCTION deny_mutation_on_append_only_tables()"
    )
    employer = predecessor()
    worker = employer.predecessor()
    execute(
        worker.INTAKE_AUTHORITY.replace(
            "AND NEW.kind='worker'", "AND NEW.kind IN ('worker','employer')"
        )
    )
    execute(
        worker.predecessor().WORKFLOW_FUNCTION.replace(
            "CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1
        )
    )
    execute(employer.result_authority())
    for prior in (worker, employer):
        execute(prior.OUTPUT_AUTHORITY.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1))
    for function in reversed(FUNCTIONS):
        execute(f"DROP FUNCTION {function}")
    worker.check("intake_links", "ck_intake_links_parent_shape", parent_shape(False))
    worker.check(
        "intake_review_payloads",
        "intake_review_payloads_dependency_refs_check",
        "dependency_refs='{}'::jsonb",
    )
    op.drop_constraint("ck_finalization_reuse_shape", "intake_finalizations", type_="check")
    output_constraints(False)
    shapes(False)
