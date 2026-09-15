"""PR C initial new-worker finalization; employer/linking expansion remains pending."""

import importlib.util
from pathlib import Path
from types import ModuleType

import sqlalchemy as sa
from alembic import op

revision = "0008_intake_finalization"
down_revision = "0007_intake_review_follow_up"
branch_labels = None
depends_on = None

KINDS = ("worker", "worker_contact", "worker_residence", "worker_preferences")
CANONICAL_TABLES = dict(
    zip(
        KINDS,
        ("workers", "worker_contacts", "worker_residences", "worker_preferences"),
        strict=True,
    )
)
TABLES = (
    "workers",
    "worker_contacts",
    "worker_residences",
    "worker_preferences",
    "worker_interest_selections",
    "intake_finalizations",
)
FUNCTIONS = ("guard_worker_output", "guard_finalization_results")


def execute(sql: str) -> None:
    op.execute(sa.text(sql))


def predecessor() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "intake_finalization_predecessor",
        Path(__file__).with_name("0007_intake_review_follow_up.py"),
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Required predecessor migration is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(table: str, name: str, expression: str) -> None:
    op.drop_constraint(name, table, type_="check")
    op.create_check_constraint(name, table, expression)


def upgrade() -> None:
    execute(
        "LOCK TABLE intakes, command_receipts, command_results, audit_events, "
        "entity_authorities IN SHARE ROW EXCLUSIVE MODE"
    )
    attribution = """version integer NOT NULL CHECK(version=1),
      created_at timestamptz NOT NULL, created_by uuid NOT NULL,
      updated_at timestamptz NOT NULL, updated_by uuid NOT NULL,
      CHECK(created_at=updated_at AND created_by=updated_by)"""
    execute(f"""
    CREATE TABLE workers (
      worker_id uuid PRIMARY KEY, full_name varchar(200) NOT NULL CHECK(btrim(full_name)<>''),
      {attribution}
    );
    CREATE TABLE worker_contacts (
      worker_contact_id uuid PRIMARY KEY, worker_id uuid NOT NULL UNIQUE REFERENCES workers,
      phone varchar(32) NOT NULL CHECK(btrim(phone)<>''), {attribution},
      UNIQUE(worker_id,worker_contact_id)
    );
    CREATE TABLE worker_residences (
      worker_residence_id uuid PRIMARY KEY, worker_id uuid NOT NULL UNIQUE REFERENCES workers,
      line1 varchar(200) NOT NULL CHECK(btrim(line1)<>''), line2 varchar(200),
      locality varchar(100) NOT NULL CHECK(btrim(locality)<>''), region varchar(100),
      postal_code varchar(32), country varchar(2) NOT NULL CHECK(country ~ '^[A-Z]{{2}}$'),
      {attribution}, UNIQUE(worker_id,worker_residence_id),
      CHECK(country<>'US' OR (region IS NOT NULL AND btrim(region)<>'' AND
        postal_code IS NOT NULL AND btrim(postal_code)<>''))
    );
    CREATE TABLE worker_preferences (
      worker_preferences_id uuid PRIMARY KEY, worker_id uuid NOT NULL UNIQUE REFERENCES workers,
      interests jsonb NOT NULL CHECK(jsonb_typeof(interests)='object'),
      availability jsonb NOT NULL CHECK(jsonb_typeof(availability)='object'),
      self_reported boolean NOT NULL CHECK(self_reported), {attribution},
      UNIQUE(worker_id,worker_preferences_id),
      CHECK(octet_length(interests::text)<=32768 AND octet_length(availability::text)<=32768),
      CHECK((availability ? 'mode' AND availability->>'mode' IN ('flexible','weekly')) IS TRUE),
      CHECK(((interests->>'other_description' IS NOT NULL AND
        btrim(interests->>'other_description')<>'') OR
        (jsonb_typeof(interests->'selections')='array' AND
         jsonb_array_length(interests->'selections') BETWEEN 1 AND 20)) IS TRUE)
    );
    CREATE TABLE worker_interest_selections (
      worker_preferences_id uuid NOT NULL REFERENCES worker_preferences,
      interest_id uuid NOT NULL, catalog_version integer NOT NULL,
      PRIMARY KEY(worker_preferences_id,interest_id),
      FOREIGN KEY(interest_id,catalog_version)
        REFERENCES work_interest_versions(interest_id,version)
    );
    CREATE TABLE intake_finalizations (
      intake_id uuid PRIMARY KEY REFERENCES intakes,
      command_id uuid NOT NULL UNIQUE REFERENCES command_receipts DEFERRABLE INITIALLY DEFERRED,
      review_id uuid NOT NULL, content_version integer NOT NULL CHECK(content_version>=1),
      result_version integer NOT NULL CHECK(result_version>=3),
      kind varchar(32) NOT NULL CHECK(kind='worker'),
      actor_id uuid NOT NULL, occurred_at timestamptz NOT NULL,
      FOREIGN KEY(intake_id,review_id) REFERENCES intake_reviews(intake_id,review_id)
    );
    """)
    for kind in KINDS:
        table = CANONICAL_TABLES[kind]
        execute(f"""
        ALTER TABLE entity_authorities ADD COLUMN {kind}_id uuid UNIQUE;
        ALTER TABLE entity_authorities ADD CONSTRAINT fk_entity_authorities_{kind}
          FOREIGN KEY({kind}_id) REFERENCES {table}({kind}_id) DEFERRABLE INITIALLY DEFERRED;
        ALTER TABLE intake_finalizations ADD COLUMN {kind}_id uuid NOT NULL UNIQUE;
        ALTER TABLE intake_finalizations ADD COLUMN {kind}_version integer NOT NULL
          CHECK({kind}_version=1);
        ALTER TABLE intake_finalizations ADD COLUMN {kind}_disposition varchar(16) NOT NULL
          CHECK({kind}_disposition='created');
        """)
        if kind == "worker":
            execute(
                "ALTER TABLE intake_finalizations ADD FOREIGN KEY(worker_id) REFERENCES workers"
            )
        else:
            execute(
                f"ALTER TABLE intake_finalizations ADD FOREIGN KEY(worker_id,{kind}_id) "
                f"REFERENCES {table}(worker_id,{kind}_id)"
            )
    prior = predecessor()
    commands = prior.BASE_COMMANDS + (
        ",'review_intake','follow_up_intake','create_work_interest','revise_work_interest',"
        "'finalize_intake'"
    )
    types = prior.BASE_TYPES + ",'work_interest'," + ",".join(f"'{kind}'" for kind in KINDS)
    events = (
        prior.BASE_EVENTS
        + (
            ",'intake.reviewed','intake.follow_up_recorded','work_interest.created',"
            "'work_interest.revised','intake.finalized',"
        )
        + ",".join(f"'{kind}.created'" for kind in KINDS)
    )
    primary_shape = (
        prior.BASE_SHAPE
        + prior.EXTRA_SHAPE
        + """
      OR (command_type='finalize_intake' AND result_entity_type='intake' AND
        result_event_type='intake.finalized' AND result_record_version>=3)"""
    )
    check("command_receipts", "ck_command_receipts_command_type", f"command_type IN ({commands})")
    check("command_receipts", "ck_command_receipts_result_authority_shape", primary_shape)
    result_shape = (
        primary_shape.replace("result_entity_type", "entity_type")
        .replace("result_event_type", "event_type")
        .replace("result_record_version", "result_version")
    )
    result_shape += (
        " OR (command_type='finalize_intake' AND result_version=1 AND ("
        + " OR ".join(f"(entity_type='{kind}' AND event_type='{kind}.created')" for kind in KINDS)
        + "))"
    )
    check("command_results", "ck_command_results_authority_shape", result_shape)
    for column, name in (("event_type", "event_type"), ("event_schema_name", "schema_name")):
        check("audit_events", f"ck_audit_events_{name}", f"{column} IN ({events})")
    check("audit_events", "ck_audit_events_entity_type", f"entity_type IN ({types})")
    check("entity_authorities", "ck_entity_authorities_entity_type", f"entity_type IN ({types})")
    concrete = ("employer", "employer_contact", "intake", "work_interest", *KINDS)
    check(
        "entity_authorities",
        "ck_entity_authorities_exactly_one_concrete_id",
        " OR ".join(
            f"(entity_type='{kind}' AND {kind}_id IS NOT NULL AND {kind}_id=entity_id AND "
            + " AND ".join(f"{other}_id IS NULL" for other in concrete if other != kind)
            + ")"
            for kind in concrete
        ),
    )
    check(
        "intakes",
        "ck_intakes_lifecycle_draft",
        "lifecycle_status='draft' OR (kind='worker' AND lifecycle_status='finalized')",
    )
    op.drop_constraint("uq_command_results_single_result", "command_results", type_="unique")
    execute(INTAKE_IDENTITY)
    execute(INTAKE_AUTHORITY)
    execute(RESULT_AUTHORITY)
    execute(OUTPUT_AUTHORITY)
    for table in ("command_receipts", "command_results", "intake_finalizations"):
        execute(
            f"CREATE CONSTRAINT TRIGGER guard_finalization_results AFTER INSERT ON {table} "
            "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
            "EXECUTE FUNCTION guard_finalization_results()"
        )
    for kind in KINDS:
        execute(
            "CREATE CONSTRAINT TRIGGER guard_worker_output AFTER INSERT ON "
            f"{CANONICAL_TABLES[kind]} "
            "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
            f"EXECUTE FUNCTION guard_worker_output('{kind}')"
        )
    execute(
        "CREATE CONSTRAINT TRIGGER guard_worker_output AFTER INSERT ON worker_interest_selections "
        "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
        "EXECUTE FUNCTION guard_worker_output('worker_preferences')"
    )
    for table in TABLES:
        execute(
            f"CREATE TRIGGER deny_mutation_{table} BEFORE UPDATE OR DELETE OR TRUNCATE "
            f"ON {table} FOR EACH STATEMENT "
            "EXECUTE FUNCTION deny_mutation_on_append_only_tables()"
        )
        execute(f"ALTER TABLE {table} OWNER TO golden_rose_schema_owner")
        execute(
            f"REVOKE ALL ON TABLE {table} FROM PUBLIC, golden_rose_runtime, golden_rose_migrator"
        )
        execute(f"GRANT SELECT, INSERT ON TABLE {table} TO golden_rose_runtime")
    execute("GRANT UPDATE(lifecycle_status) ON intakes TO golden_rose_runtime")
    for function in FUNCTIONS:
        execute(f"ALTER FUNCTION {function}() OWNER TO golden_rose_schema_owner")
        execute(
            f"REVOKE ALL ON FUNCTION {function}() FROM PUBLIC, golden_rose_runtime, "
            "golden_rose_migrator"
        )


INTAKE_IDENTITY = """
CREATE OR REPLACE FUNCTION guard_intake_identity() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF TG_TABLE_NAME='intakes' THEN
   IF TG_OP='INSERT' THEN
     IF NEW.lifecycle_status<>'draft' OR NEW.version<>1 OR NEW.content_version<>1 OR
       NEW.created_by<>NEW.updated_by OR NEW.created_at<>NEW.updated_at THEN
       RAISE EXCEPTION 'invalid intake initial attribution' USING ERRCODE='23514',
         CONSTRAINT='ck_intakes_initial_attribution';
     END IF;
   ELSIF (NEW.intake_id,NEW.kind,NEW.schema_version,NEW.created_at,NEW.created_by)
       IS DISTINCT FROM (OLD.intake_id,OLD.kind,OLD.schema_version,OLD.created_at,OLD.created_by)
     OR NEW.version<>OLD.version+1
     OR NEW.content_version NOT IN (OLD.content_version,OLD.content_version+1)
     OR (NEW.content_version=OLD.content_version AND NEW.content IS DISTINCT FROM OLD.content)
     OR (OLD.lifecycle_status='finalized' AND
       (NEW.lifecycle_status<>OLD.lifecycle_status OR
        NEW.content_version<>OLD.content_version)) THEN
     RAISE EXCEPTION 'invalid intake revision' USING ERRCODE='23514',
       CONSTRAINT='ck_intakes_revision_identity';
   END IF;
 ELSIF TG_OP='UPDATE' AND (NEW.intake_id,NEW.section)
   IS DISTINCT FROM (OLD.intake_id,OLD.section) THEN
   RAISE EXCEPTION 'immutable address identity' USING ERRCODE='23514',
     CONSTRAINT='ck_intake_addresses_identity';
 END IF;
 RETURN NEW;
END $$;
"""

INTAKE_AUTHORITY = """
CREATE OR REPLACE FUNCTION guard_intake_write_authority() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM command_results r JOIN audit_events a
   ON a.command_id=r.command_id AND a.entity_type=r.entity_type AND a.entity_id=r.entity_id
   WHERE r.entity_type='intake' AND r.entity_id=NEW.intake_id AND r.result_version=NEW.version
     AND r.actor_id=NEW.updated_by AND a.occurred_at=NEW.updated_at
     AND a.xmin::text=pg_current_xact_id()::text
     AND ((TG_OP='INSERT' AND r.command_type='create_intake') OR (TG_OP='UPDATE' AND (
       (r.command_type IN ('revise_intake','revise_intake_address') AND
         OLD.lifecycle_status='draft' AND NEW.lifecycle_status='draft' AND
         NEW.content_version=OLD.content_version+1)
       OR (r.command_type IN ('review_intake','follow_up_intake') AND
         NEW.lifecycle_status=OLD.lifecycle_status AND
         (r.command_type='follow_up_intake' OR OLD.lifecycle_status='draft') AND
         NEW.content_version=OLD.content_version AND NEW.content=OLD.content)
       OR (r.command_type='finalize_intake' AND OLD.lifecycle_status='draft' AND
         NEW.lifecycle_status='finalized' AND NEW.kind='worker' AND
         NEW.content_version=OLD.content_version AND NEW.content=OLD.content))))) THEN
   RAISE EXCEPTION 'missing atomic intake authority' USING
     ERRCODE='23514',CONSTRAINT='ck_intakes_atomic_authority';
 END IF;
 RETURN NULL;
END $$;
"""

RESULT_AUTHORITY = """
CREATE FUNCTION guard_finalization_results() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE c command_receipts%ROWTYPE; f intake_finalizations%ROWTYPE;
        i intakes%ROWTYPE; r intake_reviews%ROWTYPE; n integer;
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
 IF f.intake_id IS NULL OR i.intake_id IS NULL OR r.review_id IS NULL OR n<>5 OR
   (c.result_entity_id,c.result_record_version,c.actor_id,c.created_at)
      IS DISTINCT FROM (f.intake_id,f.result_version,f.actor_id,f.occurred_at) OR
   (i.kind,i.lifecycle_status,i.version,i.content_version,i.updated_by,i.updated_at)
      IS DISTINCT FROM ('worker'::varchar,'finalized'::varchar,f.result_version,
        f.content_version,f.actor_id,f.occurred_at) OR
   (r.review_id,r.outcome,r.reviewed_content_version)
      IS DISTINCT FROM (f.review_id,'intake_reviewed'::varchar,f.content_version) OR
   NOT EXISTS(SELECT 1 FROM intake_review_payloads WHERE review_id=f.review_id AND
     dependency_refs='{}'::jsonb) OR
   NOT EXISTS(SELECT 1 FROM intakes WHERE intake_id=f.intake_id AND
     xmin::text=pg_current_xact_id()::text) OR
   NOT EXISTS(SELECT 1 FROM intake_finalizations WHERE intake_id=f.intake_id AND
     xmin::text=pg_current_xact_id()::text) OR
   EXISTS(SELECT 1 FROM command_results x WHERE x.command_id=c.command_id AND NOT (
     (x.entity_type='intake' AND x.entity_id=f.intake_id AND x.result_version=f.result_version) OR
     (x.entity_type='worker' AND x.entity_id=f.worker_id AND x.result_version=f.worker_version) OR
     (x.entity_type='worker_contact' AND x.entity_id=f.worker_contact_id AND
       x.result_version=f.worker_contact_version) OR
     (x.entity_type='worker_residence' AND x.entity_id=f.worker_residence_id AND
       x.result_version=f.worker_residence_version) OR
     (x.entity_type='worker_preferences' AND x.entity_id=f.worker_preferences_id AND
       x.result_version=f.worker_preferences_version))) OR
   EXISTS(SELECT 1 FROM audit_events a WHERE a.command_id=c.command_id AND
     (a.actor_id<>f.actor_id OR a.occurred_at<>f.occurred_at OR
      a.xmin::text<>pg_current_xact_id()::text)) THEN
   RAISE EXCEPTION 'invalid finalization result group' USING ERRCODE='23514';
 END IF;
 RETURN NULL;
END $$;
"""

OUTPUT_AUTHORITY = """
CREATE FUNCTION guard_worker_output() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE v_kind text:=TG_ARGV[0]; target uuid; f intake_finalizations%ROWTYPE;
        candidate jsonb; address jsonb; prefs worker_preferences%ROWTYPE; selections jsonb;
BEGIN
 target:=(to_jsonb(NEW)->>(v_kind||'_id'))::uuid;
 SELECT * INTO f FROM intake_finalizations
   WHERE (to_jsonb(intake_finalizations)->>(v_kind||'_id'))::uuid=target;
 IF f.intake_id IS NULL OR NOT EXISTS(SELECT 1 FROM command_results r JOIN audit_events a
   ON a.command_id=r.command_id AND a.entity_type=r.entity_type AND a.entity_id=r.entity_id
   WHERE r.command_id=f.command_id AND r.entity_type=v_kind AND r.entity_id=target AND
     r.actor_id=f.actor_id AND r.result_version=1 AND r.event_type=v_kind||'.created'
     AND a.occurred_at=f.occurred_at AND a.xmin::text=pg_current_xact_id()::text) THEN
   RAISE EXCEPTION 'missing canonical output authority' USING ERRCODE='23514';
 END IF;
 IF TG_TABLE_NAME<>'worker_interest_selections' AND
   (((to_jsonb(NEW)->>'created_by')::uuid,(to_jsonb(NEW)->>'created_at')::timestamptz)
      IS DISTINCT FROM (f.actor_id,f.occurred_at)) THEN
   RAISE EXCEPTION 'wrong canonical actor or time' USING ERRCODE='23514';
 END IF;
 SELECT content INTO candidate FROM intakes WHERE intake_id=f.intake_id;
 IF v_kind='worker' AND to_jsonb(NEW)->>'full_name' IS DISTINCT FROM candidate->>'full_name' THEN
   RAISE EXCEPTION 'unreviewed worker name' USING ERRCODE='23514';
 ELSIF v_kind='worker_contact' AND to_jsonb(NEW)->>'phone' IS DISTINCT FROM candidate->>'phone' THEN
   RAISE EXCEPTION 'unreviewed worker phone' USING ERRCODE='23514';
 ELSIF v_kind='worker_residence' THEN
   SELECT jsonb_strip_nulls(to_jsonb(a)-'intake_id'-'section') INTO address
     FROM intake_addresses a WHERE intake_id=f.intake_id AND section='worker_residence';
   IF address IS NULL OR address IS DISTINCT FROM jsonb_strip_nulls(to_jsonb(NEW)-
     ARRAY['worker_residence_id','worker_id','version','created_at','created_by',
       'updated_at','updated_by']) THEN
     RAISE EXCEPTION 'unreviewed worker address' USING ERRCODE='23514';
   END IF;
 ELSIF v_kind='worker_preferences' THEN
   SELECT * INTO prefs FROM worker_preferences WHERE worker_preferences_id=target;
   IF (prefs.interests,prefs.availability) IS DISTINCT FROM
     (candidate->'interests',candidate->'availability') THEN
     RAISE EXCEPTION 'unreviewed worker preferences' USING ERRCODE='23514';
   END IF;
   SELECT COALESCE(jsonb_agg(jsonb_build_object('interest_id',interest_id,
     'catalog_version',catalog_version) ORDER BY interest_id),'[]'::jsonb) INTO selections
     FROM worker_interest_selections WHERE worker_preferences_id=target;
   IF selections IS DISTINCT FROM (SELECT COALESCE(
     jsonb_agg(value ORDER BY value->>'interest_id'),'[]'::jsonb)
     FROM jsonb_array_elements(COALESCE(prefs.interests->'selections','[]'::jsonb))) OR
     EXISTS(SELECT 1 FROM worker_interest_selections s JOIN work_interests w USING(interest_id)
       WHERE s.worker_preferences_id=target AND (NOT w.active OR w.version<>s.catalog_version)) THEN
     RAISE EXCEPTION 'invalid canonical interest selections' USING ERRCODE='23514';
   END IF;
 END IF;
 RETURN NULL;
END $$;
"""


def downgrade() -> None:
    execute(
        "LOCK TABLE "
        + ",".join(TABLES)
        + ",intakes,command_receipts,command_results,audit_events,entity_authorities "
        "IN SHARE ROW EXCLUSIVE MODE"
    )
    populated = [sa.exists(sa.select(1).select_from(sa.table(table))) for table in TABLES]
    intake_table = sa.table("intakes", sa.column("lifecycle_status"))
    receipt_table = sa.table("command_receipts", sa.column("command_type"))
    populated.extend(
        [
            sa.exists(sa.select(1).where(intake_table.c.lifecycle_status == "finalized")),
            sa.exists(sa.select(1).where(receipt_table.c.command_type == "finalize_intake")),
        ]
    )
    data = op.get_bind().execute(sa.select(sa.or_(*populated))).scalar_one()
    if data:
        raise RuntimeError("successor finalization data blocks downgrade before DDL")
    execute("SET CONSTRAINTS ALL IMMEDIATE")
    for table in ("command_receipts", "command_results", "intake_finalizations"):
        execute(f"DROP TRIGGER guard_finalization_results ON {table}")
    for table in TABLES[:-1]:
        execute(f"DROP TRIGGER guard_worker_output ON {table}")
    for function in FUNCTIONS:
        execute(f"DROP FUNCTION {function}()")
    prior = predecessor()
    prior.shapes(True)
    execute(prior.INTAKE_FUNCTIONS)
    check("intakes", "ck_intakes_lifecycle_draft", "lifecycle_status='draft'")
    execute("REVOKE UPDATE(lifecycle_status) ON intakes FROM golden_rose_runtime")
    for kind in KINDS:
        op.drop_column("entity_authorities", f"{kind}_id")
    for table in reversed(TABLES):
        op.drop_table(table)
    op.create_unique_constraint(
        "uq_command_results_single_result", "command_results", ["command_id"]
    )
