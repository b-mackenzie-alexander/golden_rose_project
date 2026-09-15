"""Add new-employer finalization without replaying the applied worker migration."""

import importlib.util
from pathlib import Path
from types import ModuleType

import sqlalchemy as sa
from alembic import op

revision = "0008a_employer_finalization"
down_revision = "0008_intake_finalization"
branch_labels = None
depends_on = None

TABLES = {
    "employer_contact_details": "employer_contact_details",
    "employer_address": "employer_addresses",
    "worksite": "worksites",
    "staffing_request": "staffing_requests",
}
EMPLOYER_KINDS = ("employer", "employer_contact", *TABLES)


def predecessor() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "worker_finalization_predecessor", Path(__file__).with_name("0008_intake_finalization.py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Required worker predecessor unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def execute(sql: str) -> None:
    op.execute(sa.text(sql))


def shapes(expanded: bool) -> None:
    worker = predecessor()
    prior = worker.predecessor()
    kinds = (*worker.KINDS, *TABLES) if expanded else worker.KINDS
    types = prior.BASE_TYPES + ",'work_interest'," + ",".join(f"'{kind}'" for kind in kinds)
    events = (
        prior.BASE_EVENTS
        + ",'intake.reviewed','intake.follow_up_recorded',"
        + ("'work_interest.created','work_interest.revised','intake.finalized',")
        + ",".join(f"'{kind}.created'" for kind in kinds)
    )
    primary = (
        prior.BASE_SHAPE
        + prior.EXTRA_SHAPE
        + """ OR
      (command_type='finalize_intake' AND result_entity_type='intake' AND
       result_event_type='intake.finalized' AND result_record_version>=3)"""
    )
    result = (
        primary.replace("result_entity_type", "entity_type")
        .replace("result_event_type", "event_type")
        .replace("result_record_version", "result_version")
    )
    created = (*worker.KINDS, *EMPLOYER_KINDS) if expanded else worker.KINDS
    result += (
        " OR (command_type='finalize_intake' AND result_version=1 AND ("
        + " OR ".join(f"(entity_type='{kind}' AND event_type='{kind}.created')" for kind in created)
        + "))"
    )
    worker.check("command_results", "ck_command_results_authority_shape", result)
    for column, name in (("event_type", "event_type"), ("event_schema_name", "schema_name")):
        worker.check("audit_events", f"ck_audit_events_{name}", f"{column} IN ({events})")
    worker.check("audit_events", "ck_audit_events_entity_type", f"entity_type IN ({types})")
    worker.check(
        "entity_authorities", "ck_entity_authorities_entity_type", f"entity_type IN ({types})"
    )
    concrete = ("employer", "employer_contact", "intake", "work_interest", *kinds)
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
    worker.check(
        "intakes",
        "ck_intakes_lifecycle_draft",
        "lifecycle_status IN ('draft','finalized')"
        if expanded
        else "lifecycle_status='draft' OR (kind='worker' AND lifecycle_status='finalized')",
    )


def upgrade() -> None:
    execute(
        "LOCK TABLE intakes,intake_finalizations,employers,employer_contacts,entity_authorities,"
        "command_results,audit_events IN SHARE ROW EXCLUSIVE MODE"
    )
    attribution = """version integer NOT NULL CHECK(version=1), created_at timestamptz NOT NULL,
      updated_at timestamptz NOT NULL, created_by uuid NOT NULL, updated_by uuid NOT NULL,
      CHECK(created_at=updated_at AND created_by=updated_by)"""
    address = """line1 varchar(200), line2 varchar(200), locality varchar(100), region varchar(100),
      postal_code varchar(32), country varchar(2)"""
    complete = """(line1 IS NOT NULL AND btrim(line1)<>''
      AND locality IS NOT NULL AND btrim(locality)<>''
      AND country IS NOT NULL AND country ~ '^[A-Z]{2}$' AND (country<>'US' OR
      (region IS NOT NULL AND btrim(region)<>''
       AND postal_code IS NOT NULL AND btrim(postal_code)<>'')))"""
    execute(f"""
    CREATE TABLE employer_contact_details (
      employer_contact_details_id uuid PRIMARY KEY, employer_id uuid NOT NULL,
      employer_contact_id uuid NOT NULL UNIQUE,
      representative_name varchar(200) NOT NULL CHECK(btrim(representative_name)<>''),
      phone varchar(40) NOT NULL CHECK(btrim(phone)<>''), {address}, {attribution},
      FOREIGN KEY(employer_id,employer_contact_id)
        REFERENCES employer_contacts(employer_id,employer_contact_id),
      UNIQUE(employer_id,employer_contact_details_id),
      CHECK(({complete}) OR (line1 IS NULL AND line2 IS NULL AND locality IS NULL
        AND region IS NULL AND postal_code IS NULL AND country IS NULL))
    );
    CREATE TABLE employer_addresses (
      employer_address_id uuid PRIMARY KEY, employer_id uuid NOT NULL REFERENCES employers,
      purpose varchar(32) NOT NULL CHECK(purpose='business'), {address}, {attribution},
      CHECK({complete}), UNIQUE(employer_id,employer_address_id)
    );
    CREATE TABLE worksites (
      worksite_id uuid PRIMARY KEY, employer_id uuid NOT NULL REFERENCES employers,
      location_verification_status varchar(32) NOT NULL
        CHECK(location_verification_status='supplied'),
      service_area_status varchar(32) NOT NULL CHECK(service_area_status='unassigned'),
      map_area_status varchar(32) NOT NULL CHECK(map_area_status='pending'),
      {address}, {attribution},
      CHECK({complete}), UNIQUE(employer_id,worksite_id)
    );
    CREATE TABLE staffing_requests (
      staffing_request_id uuid PRIMARY KEY, employer_id uuid NOT NULL REFERENCES employers,
      employer_contact_id uuid NOT NULL, worksite_id uuid NOT NULL, employer_address_id uuid,
      request_type varchar(32) NOT NULL CHECK(request_type IN ('household','general_labor')),
      request_status varchar(32) NOT NULL CHECK(request_status='draft'),
      source_channel varchar(32) NOT NULL CHECK(source_channel='staff_entry'),
      received_at timestamptz NOT NULL,
      role_title varchar(200) NOT NULL CHECK(btrim(role_title)<>''),
      duties_summary varchar(1000) NOT NULL CHECK(btrim(duties_summary)<>''),
      worker_count integer NOT NULL CHECK(worker_count BETWEEN 1 AND 1000),
      schedule jsonb NOT NULL CHECK(jsonb_typeof(schedule)='object'
        AND octet_length(schedule::text)<=32768),
      offer jsonb NOT NULL CHECK(jsonb_typeof(offer)='object'
        AND octet_length(offer::text)<=32768), {attribution},
      CHECK(received_at=created_at),
      CHECK((request_type='household')=(employer_address_id IS NULL)),
      CHECK((schedule->>'mode' IN ('to_be_discussed','specified')) IS TRUE),
      CHECK((offer ?& ARRAY['minimum','currency','basis','per_worker']
        AND offer->>'minimum' IS NOT NULL AND offer->>'currency' IS NOT NULL
        AND offer->>'basis' IS NOT NULL AND offer->'per_worker'='true'::jsonb) IS TRUE),
      FOREIGN KEY(employer_id,employer_contact_id)
        REFERENCES employer_contacts(employer_id,employer_contact_id),
      FOREIGN KEY(employer_id,worksite_id) REFERENCES worksites(employer_id,worksite_id),
      FOREIGN KEY(employer_id,employer_address_id)
        REFERENCES employer_addresses(employer_id,employer_address_id),
      UNIQUE(employer_id,staffing_request_id)
    );
    """)
    worker = predecessor()
    for table in ("employer_addresses", "worksites"):
        for column in ("line1", "locality", "country"):
            op.alter_column(table, column, nullable=False)
    for kind, table in TABLES.items():
        execute(
            f"ALTER TABLE entity_authorities ADD COLUMN {kind}_id uuid UNIQUE "
            f"REFERENCES {table}({kind}_id) DEFERRABLE INITIALLY DEFERRED"
        )
    for kind in worker.KINDS:
        for suffix in ("id", "version", "disposition"):
            op.alter_column("intake_finalizations", f"{kind}_{suffix}", nullable=True)
    for kind in EMPLOYER_KINDS:
        execute(f"""ALTER TABLE intake_finalizations ADD COLUMN {kind}_id uuid UNIQUE;
          ALTER TABLE intake_finalizations ADD COLUMN {kind}_version integer
            CHECK({kind}_version=1);
          ALTER TABLE intake_finalizations ADD COLUMN {kind}_disposition varchar(16)
            CHECK({kind}_disposition='created');""")
        table = {"employer": "employers", "employer_contact": "employer_contacts", **TABLES}[kind]
        if kind == "employer":
            execute(
                "ALTER TABLE intake_finalizations ADD FOREIGN KEY(employer_id) REFERENCES employers"
            )
        else:
            execute(
                f"ALTER TABLE intake_finalizations ADD FOREIGN KEY(employer_id,{kind}_id) "
                f"REFERENCES {table}(employer_id,{kind}_id)"
            )
    op.drop_constraint("intake_finalizations_kind_check", "intake_finalizations", type_="check")
    branches = []
    for label, required, absent in (
        ("worker", worker.KINDS, EMPLOYER_KINDS),
        ("employer", tuple(k for k in EMPLOYER_KINDS if k != "employer_address"), worker.KINDS),
    ):
        clauses = [f"kind='{label}'"]
        clauses += [
            f"{kind}_{suffix} IS NOT NULL"
            for kind in required
            for suffix in ("id", "version", "disposition")
        ]
        clauses += [
            f"{kind}_{suffix} IS NULL"
            for kind in absent
            for suffix in ("id", "version", "disposition")
        ]
        if label == "employer":
            clauses.append(
                "((employer_address_id IS NULL AND employer_address_version IS NULL "
                "AND employer_address_disposition IS NULL) OR (employer_address_id IS NOT NULL "
                "AND employer_address_version IS NOT NULL "
                "AND employer_address_disposition IS NOT NULL))"
            )
        branches.append("(" + " AND ".join(clauses) + ")")
    op.create_check_constraint(
        "ck_intake_finalizations_kind_shape", "intake_finalizations", " OR ".join(branches)
    )
    shapes(True)
    execute(
        worker.INTAKE_AUTHORITY.replace(
            "AND NEW.kind='worker'", "AND NEW.kind IN ('worker','employer')"
        )
    )
    execute(result_authority())
    execute(OUTPUT_AUTHORITY)
    for kind, table in {
        "employer": "employers",
        "employer_contact": "employer_contacts",
        **TABLES,
    }.items():
        execute(
            f"CREATE CONSTRAINT TRIGGER guard_employer_output AFTER INSERT ON {table} "
            "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
            f"EXECUTE FUNCTION guard_employer_output('{kind}')"
        )
    for table in TABLES.values():
        execute(
            f"CREATE TRIGGER deny_mutation_{table} BEFORE UPDATE OR DELETE OR TRUNCATE "
            f"ON {table} FOR EACH STATEMENT EXECUTE FUNCTION deny_mutation_on_append_only_tables()"
        )
        execute(f"ALTER TABLE {table} OWNER TO golden_rose_schema_owner")
        execute(f"REVOKE ALL ON TABLE {table} FROM PUBLIC,golden_rose_runtime,golden_rose_migrator")
        execute(f"GRANT SELECT,INSERT ON TABLE {table} TO golden_rose_runtime")
    execute("ALTER FUNCTION guard_employer_output() OWNER TO golden_rose_schema_owner")
    execute(
        "REVOKE ALL ON FUNCTION guard_employer_output() "
        "FROM PUBLIC,golden_rose_runtime,golden_rose_migrator"
    )


def result_authority() -> str:
    return """
    CREATE OR REPLACE FUNCTION guard_finalization_results() RETURNS trigger LANGUAGE plpgsql
    SET search_path=pg_catalog,public,pg_temp AS $$
    DECLARE c command_receipts%ROWTYPE; f intake_finalizations%ROWTYPE; i intakes%ROWTYPE;
      r intake_reviews%ROWTYPE; n integer; expected integer;
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
      expected:=CASE WHEN f.kind='worker'
        THEN 5 WHEN f.employer_address_id IS NULL THEN 6 ELSE 7 END;
      IF f.intake_id IS NULL OR i.intake_id IS NULL OR r.review_id IS NULL OR n<>expected OR
        (c.result_entity_id,c.result_record_version,c.actor_id,c.created_at) IS DISTINCT FROM
          (f.intake_id,f.result_version,f.actor_id,f.occurred_at) OR
        (i.kind,i.lifecycle_status,i.version,i.content_version,i.updated_by,i.updated_at)
          IS DISTINCT FROM (f.kind,'finalized'::varchar,f.result_version,
            f.content_version,f.actor_id,f.occurred_at) OR
        (r.review_id,r.outcome,r.reviewed_content_version) IS DISTINCT FROM
          (f.review_id,'intake_reviewed'::varchar,f.content_version) OR
        NOT EXISTS(SELECT 1 FROM intake_review_payloads WHERE review_id=f.review_id
          AND dependency_refs='{}'::jsonb) OR
        NOT EXISTS(SELECT 1 FROM intakes WHERE intake_id=f.intake_id
          AND xmin::text=pg_current_xact_id()::text) OR
        NOT EXISTS(SELECT 1 FROM intake_finalizations WHERE intake_id=f.intake_id
          AND xmin::text=pg_current_xact_id()::text) OR
        EXISTS(SELECT 1 FROM command_results x WHERE x.command_id=c.command_id AND NOT COALESCE((
          (x.entity_type='intake' AND x.entity_id=f.intake_id
            AND x.result_version=f.result_version) OR
          (x.entity_type='worker' AND x.entity_id=f.worker_id
            AND x.result_version=f.worker_version) OR
          (x.entity_type='worker_contact' AND x.entity_id=f.worker_contact_id
            AND x.result_version=f.worker_contact_version) OR
          (x.entity_type='worker_residence' AND x.entity_id=f.worker_residence_id
            AND x.result_version=f.worker_residence_version) OR
          (x.entity_type='worker_preferences' AND x.entity_id=f.worker_preferences_id
            AND x.result_version=f.worker_preferences_version) OR
          (x.entity_type='employer' AND x.entity_id=f.employer_id
            AND x.result_version=f.employer_version) OR
          (x.entity_type='employer_contact' AND x.entity_id=f.employer_contact_id
            AND x.result_version=f.employer_contact_version) OR
          (x.entity_type='employer_contact_details' AND x.entity_id=f.employer_contact_details_id
            AND x.result_version=f.employer_contact_details_version) OR
          (x.entity_type='employer_address' AND x.entity_id=f.employer_address_id
            AND x.result_version=f.employer_address_version) OR
          (x.entity_type='worksite' AND x.entity_id=f.worksite_id
            AND x.result_version=f.worksite_version) OR
          (x.entity_type='staffing_request' AND x.entity_id=f.staffing_request_id
            AND x.result_version=f.staffing_request_version)),false)) OR
        EXISTS(SELECT 1 FROM audit_events a WHERE a.command_id=c.command_id AND
          (a.actor_id<>f.actor_id OR a.occurred_at<>f.occurred_at OR
            a.xmin::text<>pg_current_xact_id()::text)) THEN
        RAISE EXCEPTION 'invalid finalization result group' USING ERRCODE='23514';
      END IF;
      IF f.kind='employer' AND NOT EXISTS(SELECT 1 FROM employers e JOIN staffing_requests s
        ON s.employer_id=e.employer_id WHERE e.employer_id=f.employer_id
        AND s.staffing_request_id=f.staffing_request_id
        AND e.xmin::text=pg_current_xact_id()::text AND s.xmin::text=pg_current_xact_id()::text
        AND s.employer_contact_id=f.employer_contact_id AND s.worksite_id=f.worksite_id
        AND s.employer_address_id IS NOT DISTINCT FROM f.employer_address_id
        AND s.request_type=CASE WHEN e.employer_type='household'
          THEN 'household' ELSE 'general_labor' END
        AND EXISTS(SELECT 1 FROM employer_contact_details d
          WHERE d.employer_contact_details_id=f.employer_contact_details_id
          AND d.employer_contact_id=f.employer_contact_id
          AND d.xmin::text=pg_current_xact_id()::text)
        AND EXISTS(SELECT 1 FROM employer_contacts ec
          WHERE ec.employer_contact_id=f.employer_contact_id
          AND ec.xmin::text=pg_current_xact_id()::text)
        AND EXISTS(SELECT 1 FROM worksites w WHERE w.worksite_id=f.worksite_id
          AND w.xmin::text=pg_current_xact_id()::text)
        AND (f.employer_address_id IS NULL OR EXISTS(SELECT 1 FROM employer_addresses ea
          WHERE ea.employer_address_id=f.employer_address_id
          AND ea.xmin::text=pg_current_xact_id()::text))) THEN
        RAISE EXCEPTION 'wrong employer output parents' USING ERRCODE='23514';
      END IF;
      RETURN NULL;
    END $$;
    """


OUTPUT_AUTHORITY = """
CREATE FUNCTION guard_employer_output() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE v_kind text:=TG_ARGV[0]; target uuid; f intake_finalizations%ROWTYPE;
  candidate jsonb; expected_address jsonb; actual jsonb:=to_jsonb(NEW);
BEGIN
  target:=(actual->>(v_kind||'_id'))::uuid;
  SELECT * INTO f FROM intake_finalizations WHERE kind='employer' AND
    (to_jsonb(intake_finalizations)->>(v_kind||'_id'))::uuid=target;
  IF f.intake_id IS NULL AND v_kind IN ('employer','employer_contact') THEN
    IF EXISTS(SELECT 1 FROM command_results WHERE entity_type=v_kind AND entity_id=target
      AND command_type='finalize_intake') THEN
      RAISE EXCEPTION 'missing employer finalization' USING ERRCODE='23514';
    END IF;
    RETURN NULL;
  END IF;
  IF f.intake_id IS NULL OR NOT EXISTS(SELECT 1 FROM command_results r JOIN audit_events a
    ON a.command_id=r.command_id AND a.entity_type=r.entity_type AND a.entity_id=r.entity_id
    WHERE r.command_id=f.command_id AND r.entity_type=v_kind AND r.entity_id=target
      AND r.result_version=1
      AND r.actor_id=f.actor_id AND r.event_type=v_kind||'.created' AND a.occurred_at=f.occurred_at
      AND a.xmin::text=pg_current_xact_id()::text) OR
    ((actual->>'created_by')::uuid,(actual->>'created_at')::timestamptz,
      (actual->>'updated_by')::uuid,(actual->>'updated_at')::timestamptz,
      (actual->>'version')::integer)
      IS DISTINCT FROM (f.actor_id,f.occurred_at,f.actor_id,f.occurred_at,1) OR
    (v_kind='employer' AND
      (actual->>'received_at')::timestamptz IS DISTINCT FROM f.occurred_at) THEN
    RAISE EXCEPTION 'missing employer output authority' USING ERRCODE='23514';
  END IF;
  SELECT content INTO candidate FROM intakes WHERE intake_id=f.intake_id;
  IF v_kind='employer' AND (actual->>'employer_type',actual->>'display_name') IS DISTINCT FROM
    (candidate->>'employer_type',candidate->>'display_name') THEN
    RAISE EXCEPTION 'unreviewed employer identity' USING ERRCODE='23514';
  ELSIF v_kind='employer_contact' AND actual->>'full_name'
    IS DISTINCT FROM candidate->>'representative_name' THEN
    RAISE EXCEPTION 'unreviewed representative' USING ERRCODE='23514';
  ELSIF v_kind='employer_contact_details'
    AND (actual->>'representative_name',actual->>'phone') IS DISTINCT FROM
    (candidate->>'representative_name',candidate->>'phone') THEN
    RAISE EXCEPTION 'unreviewed contact details' USING ERRCODE='23514';
  ELSIF v_kind='staffing_request' AND (actual->'role_title',actual->'duties_summary',
    actual->'worker_count',actual->'schedule',actual->'offer') IS DISTINCT FROM
    (candidate->'role_title',candidate->'duties_summary',candidate->'worker_count',
      candidate->'schedule',candidate->'offer') THEN
    RAISE EXCEPTION 'unreviewed staffing request' USING ERRCODE='23514';
  END IF;
  IF v_kind IN ('employer_contact_details','employer_address','worksite') THEN
    SELECT jsonb_strip_nulls(to_jsonb(a)-'intake_id'-'section') INTO expected_address
      FROM intake_addresses a WHERE intake_id=f.intake_id
      AND section=CASE WHEN v_kind='worksite' THEN 'worksite_address' ELSE 'party_address' END;
    IF v_kind='employer_contact_details' AND candidate->>'employer_type'='business' THEN
      expected_address:='{}'::jsonb;
    END IF;
    IF expected_address IS NULL OR expected_address IS DISTINCT FROM
      jsonb_strip_nulls(jsonb_build_object(
      'line1',actual->'line1','line2',actual->'line2',
      'locality',actual->'locality','region',actual->'region',
      'postal_code',actual->'postal_code','country',actual->'country')) THEN
      RAISE EXCEPTION 'unreviewed employer address' USING ERRCODE='23514';
    END IF;
  END IF;
  RETURN NULL;
END $$;
"""


def downgrade() -> None:
    execute(
        "LOCK TABLE "
        + ",".join(TABLES.values())
        + ",intake_finalizations,entity_authorities,command_results,audit_events,intakes "
        "IN SHARE ROW EXCLUSIVE MODE"
    )
    f = sa.table("intake_finalizations", sa.column("kind"))
    populated = [sa.exists(sa.select(1).select_from(sa.table(table))) for table in TABLES.values()]
    populated.append(sa.exists(sa.select(1).where(f.c.kind == "employer")))
    if op.get_bind().execute(sa.select(sa.or_(*populated))).scalar_one():
        raise RuntimeError("employer finalization data blocks downgrade before DDL")
    execute("SET CONSTRAINTS ALL IMMEDIATE")
    for table in ("employers", "employer_contacts", *TABLES.values()):
        execute(f"DROP TRIGGER guard_employer_output ON {table}")
    execute("DROP FUNCTION guard_employer_output()")
    worker = predecessor()
    execute(worker.RESULT_AUTHORITY.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1))
    execute(worker.INTAKE_AUTHORITY)
    shapes(False)
    op.drop_constraint("ck_intake_finalizations_kind_shape", "intake_finalizations", type_="check")
    for kind in EMPLOYER_KINDS:
        for suffix in ("id", "version", "disposition"):
            op.drop_column("intake_finalizations", f"{kind}_{suffix}")
    for kind in worker.KINDS:
        for suffix in ("id", "version", "disposition"):
            op.alter_column("intake_finalizations", f"{kind}_{suffix}", nullable=False)
    op.create_check_constraint(
        "intake_finalizations_kind_check", "intake_finalizations", "kind='worker'"
    )
    for kind in TABLES:
        op.drop_column("entity_authorities", f"{kind}_id")
    for table in reversed(tuple(TABLES.values())):
        op.drop_table(table)
