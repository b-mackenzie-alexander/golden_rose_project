"""Version-bound intake review, follow-up and governed catalog history."""

import sqlalchemy as sa
from alembic import op

revision = "0007_intake_review_follow_up"
down_revision = "0006_intake_drafts"
branch_labels = None
depends_on = None

TABLES = (
    "work_interests",
    "work_interest_versions",
    "intake_reviews",
    "intake_review_payloads",
    "intake_follow_up_events",
    "intake_history_payloads",
)
FUNCTIONS = (
    "guard_intake_workflow_authority",
    "guard_work_interest_identity",
    "guard_work_interest_authority",
)
BASE_COMMANDS = (
    "'create_draft_employer','create_employer_contact','revise_draft_e"
    "mployer','create_intake','revise_intake','revise_intake_address'"
)
BASE_EVENTS = (
    "'employer.created','employer_contact.created','employer.draft_rev"
    "ised','intake.created','intake.revised'"
)
BASE_TYPES = "'employer','employer_contact','intake'"
BASE_SHAPE = """(command_type='create_draft_employer' AND result_entity_type='employer' AND
result_event_type='employer.created' AND result_record_version=1)
OR (command_type='create_employer_contact' AND result_entity_type='employer_contact' AND
result_event_type='employer_contact.created' AND result_record_version=1)
OR (command_type='revise_draft_employer' AND result_entity_type='employer' AND
result_event_type='employer.draft_revised' AND result_record_version>=2)
OR (command_type='create_intake' AND result_entity_type='intake' AND
result_event_type='intake.created' AND result_record_version=1)
OR (command_type IN ('revise_intake','revise_intake_address') AND
result_entity_type='intake' AND result_event_type='intake.revised' AND
result_record_version>=2)"""
EXTRA_SHAPE = """OR (command_type='review_intake' AND result_entity_type='intake' AND
result_event_type='intake.reviewed' AND result_record_version>=2)
OR (command_type='follow_up_intake' AND result_entity_type='intake' AND
result_event_type='intake.follow_up_recorded' AND result_record_version>=2)
OR (command_type='create_work_interest' AND result_entity_type='work_interest' AND
result_event_type='work_interest.created' AND result_record_version=1)
OR (command_type='revise_work_interest' AND result_entity_type='work_interest' AND
result_event_type='work_interest.revised' AND result_record_version>=2)"""


def execute(sql: str) -> None:
    op.execute(sa.text(sql))


def check(table: str, name: str, expression: str) -> None:
    op.drop_constraint(name, table, type_="check")
    op.create_check_constraint(name, table, expression)


def shapes(successor: bool) -> None:
    types = BASE_TYPES + (",'work_interest'" if successor else "")
    commands = BASE_COMMANDS + (
        ",'review_intake','follow_up_intake','create_work_interest','revise_work_interest'"
        if successor
        else ""
    )
    events = BASE_EVENTS + (
        (
            ",'intake.reviewed','intake.follow_up_recorded','work_interest.cre"
            "ated','work_interest.revised'"
        )
        if successor
        else ""
    )
    shape = BASE_SHAPE + (EXTRA_SHAPE if successor else "")
    check("command_receipts", "ck_command_receipts_command_type", f"command_type IN ({commands})")
    check("command_receipts", "ck_command_receipts_entity_type", f"result_entity_type IN ({types})")
    check("command_receipts", "ck_command_receipts_result_authority_shape", shape)
    check(
        "command_results",
        "ck_command_results_authority_shape",
        shape.replace("result_entity_type", "entity_type")
        .replace("result_event_type", "event_type")
        .replace("result_record_version", "result_version"),
    )
    for column, name in [("event_type", "event_type"), ("event_schema_name", "schema_name")]:
        check("audit_events", f"ck_audit_events_{name}", f"{column} IN ({events})")
    check("audit_events", "ck_audit_events_entity_type", f"entity_type IN ({types})")
    check("entity_authorities", "ck_entity_authorities_entity_type", f"entity_type IN ({types})")
    concrete = ["employer", "employer_contact", "intake"] + (["work_interest"] if successor else [])
    check(
        "entity_authorities",
        "ck_entity_authorities_exactly_one_concrete_id",
        " OR ".join(
            "("
            + f"entity_type='{kind}' AND {kind}_id IS NOT NULL AND {kind}_id=entity_id AND "
            + " AND ".join(f"{other}_id IS NULL" for other in concrete if other != kind)
            + ")"
            for kind in concrete
        ),
    )


def upgrade() -> None:
    execute(
        "LOCK TABLE intakes, intake_addresses, command_receipts, command_r"
        "esults, audit_events, entity_authorities IN SHARE ROW EXCLUSIVE M"
        "ODE"
    )
    execute("""
    CREATE TABLE work_interests (
      interest_id uuid PRIMARY KEY, code varchar(64) NOT NULL UNIQUE,
      version integer NOT NULL CHECK(version>=1),
      label_en varchar(100) NOT NULL CHECK(btrim(label_en)<>''),
      label_es varchar(100) NOT NULL CHECK(btrim(label_es)<>''), active boolean NOT
NULL,
      created_at timestamptz NOT NULL, created_by uuid NOT NULL,
      updated_at timestamptz NOT NULL, updated_by uuid NOT NULL,
      CONSTRAINT ck_work_interests_code CHECK(code ~ '^[a-z0-9_]{1,64}$')
    );
    CREATE TABLE work_interest_versions (
      interest_id uuid NOT NULL REFERENCES work_interests(interest_id),
      version integer NOT NULL CHECK(version>=1),
      label_en varchar(100) NOT NULL CHECK(btrim(label_en)<>''),
      label_es varchar(100) NOT NULL CHECK(btrim(label_es)<>''), active boolean NOT
NULL,
      actor_id uuid NOT NULL, occurred_at timestamptz NOT NULL,
      command_id uuid NOT NULL UNIQUE REFERENCES command_receipts(command_id) DEFERRABLE
INITIALLY DEFERRED,
      PRIMARY KEY(interest_id,version)
    );
    ALTER TABLE entity_authorities ADD COLUMN work_interest_id uuid UNIQUE;
    ALTER TABLE entity_authorities ADD CONSTRAINT fk_entity_authorities_work_interest
      FOREIGN KEY(work_interest_id) REFERENCES work_interests(interest_id) DEFERRABLE
INITIALLY DEFERRED;
    CREATE TABLE intake_reviews (
      review_id uuid PRIMARY KEY, intake_id uuid NOT NULL REFERENCES intakes(intake_id),
      command_id uuid NOT NULL UNIQUE REFERENCES command_receipts(command_id) DEFERRABLE
INITIALLY DEFERRED,
      event_id uuid NOT NULL UNIQUE REFERENCES audit_events(audit_event_id) DEFERRABLE
INITIALLY DEFERRED,
      reviewed_record_version integer NOT NULL CHECK(reviewed_record_version>=1),
      reviewed_content_version integer NOT NULL CHECK(reviewed_content_version>=1 AND
reviewed_content_version<=reviewed_record_version),
      result_version integer NOT NULL CHECK(result_version=reviewed_record_version+1),
      outcome varchar(32) NOT NULL CHECK(outcome IN
('intake_reviewed','needs_follow_up')),
      actor_id uuid NOT NULL, actor_display_name varchar(200) NOT NULL
CHECK(btrim(actor_display_name)<>''),
      occurred_at timestamptz NOT NULL,
      UNIQUE(intake_id,review_id), UNIQUE(intake_id,result_version)
    );
    CREATE TABLE intake_review_payloads (
      review_id uuid PRIMARY KEY REFERENCES intake_reviews(review_id) DEFERRABLE
INITIALLY DEFERRED,
      reviewed_content jsonb NOT NULL CHECK(jsonb_typeof(reviewed_content)='object'),
      note varchar(512) CHECK(note IS NULL OR btrim(note)<>''),
      dependency_refs jsonb NOT NULL DEFAULT '{}' CHECK(dependency_refs='{}'::jsonb)
    );
    ALTER TABLE intake_reviews ADD CONSTRAINT fk_intake_reviews_required_payload
      FOREIGN KEY(review_id) REFERENCES intake_review_payloads(review_id) DEFERRABLE
INITIALLY DEFERRED;
    CREATE TABLE intake_follow_up_events (
      event_id uuid PRIMARY KEY REFERENCES audit_events(audit_event_id) DEFERRABLE
INITIALLY DEFERRED,
      intake_id uuid NOT NULL REFERENCES intakes(intake_id),
      command_id uuid NOT NULL UNIQUE REFERENCES command_receipts(command_id) DEFERRABLE
INITIALLY DEFERRED,
      version integer NOT NULL CHECK(version>=2), content_version integer NOT NULL
CHECK(content_version>=1 AND content_version<version),
      action varchar(32) NOT NULL CHECK(action IN
('needs_follow_up','reschedule','reassign','attempt')),
      actor_id uuid NOT NULL, actor_display_name varchar(200) NOT NULL
CHECK(btrim(actor_display_name)<>''),
      occurred_at timestamptz NOT NULL, owner_staff_id uuid NOT NULL,
      next_follow_up_at timestamptz NOT NULL, time_zone varchar(100) NOT NULL
CHECK(btrim(time_zone)<>''),
      reason_code varchar(32), method varchar(32), outcome varchar(64), review_id uuid,
      UNIQUE(intake_id,version),
      FOREIGN KEY(intake_id,review_id) REFERENCES intake_reviews(intake_id,review_id)
DEFERRABLE INITIALLY DEFERRED,
      CONSTRAINT ck_intake_follow_up_shape CHECK(
        (action='needs_follow_up' AND review_id IS NOT NULL AND reason_code IS NOT NULL
AND reason_code IN ('missing_information','clarification','other') AND method IS NULL
AND outcome IS NULL)
        OR (action IN ('reschedule','reassign') AND review_id IS NULL AND reason_code IS
NULL AND method IS NULL AND outcome IS NULL)
        OR (action='attempt' AND review_id IS NULL AND reason_code IS NULL AND method IS
NOT NULL AND method IN ('phone','email','in_person','other') AND outcome IS NOT NULL AND
outcome IN
('no_answer','voicemail_left','callback_requested','contact_reached_information_pending','invalid_contact_information','information_received','other')))
    );
    CREATE TABLE intake_history_payloads (
      event_id uuid PRIMARY KEY REFERENCES intake_follow_up_events(event_id) DEFERRABLE
INITIALLY DEFERRED,
      reason_text varchar(512) NOT NULL CHECK(btrim(reason_text)<>''), note varchar(512)
CHECK(note IS NULL OR btrim(note)<>'')
    );
    ALTER TABLE intake_follow_up_events ADD CONSTRAINT
fk_intake_follow_up_required_payload
      FOREIGN KEY(event_id) REFERENCES intake_history_payloads(event_id) DEFERRABLE
INITIALLY DEFERRED;
""")
    shapes(True)
    check(
        "intakes", "ck_intakes_content_version", "content_version>=1 AND content_version<=version"
    )
    execute(INTAKE_FUNCTIONS)
    execute(WORKFLOW_FUNCTION)
    execute(CATALOG_FUNCTIONS)
    for table in (
        "intake_reviews",
        "intake_review_payloads",
        "intake_follow_up_events",
        "intake_history_payloads",
        "audit_events",
    ):
        execute(
            f"CREATE CONSTRAINT TRIGGER guard_intake_workflow_authority AFTER INSERT ON {table} "
            "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
            "EXECUTE FUNCTION guard_intake_workflow_authority()"
        )
    execute(
        "CREATE TRIGGER guard_work_interest_identity BEFORE INSERT OR UPDA"
        "TE ON work_interests FOR EACH ROW EXECUTE FUNCTION guard_work_int"
        "erest_identity()"
    )
    for table in ("work_interests", "work_interest_versions", "audit_events"):
        execute(
            f"CREATE CONSTRAINT TRIGGER guard_work_interest_authority AFTER INSERT"
            f"{' OR UPDATE' if table == 'work_interests' else ''} ON {table} "
            "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
            "EXECUTE FUNCTION guard_work_interest_authority()"
        )
    for table in TABLES:
        operations = (
            "DELETE OR TRUNCATE" if table == "work_interests" else "UPDATE OR DELETE OR TRUNCATE"
        )
        execute(
            f"CREATE TRIGGER deny_mutation_{table} BEFORE {operations} ON {table} "
            "FOR EACH STATEMENT EXECUTE FUNCTION deny_mutation_on_append_only_tables()"
        )
        execute(f"ALTER TABLE {table} OWNER TO golden_rose_schema_owner")
        execute(
            f"REVOKE ALL ON TABLE {table} FROM PUBLIC, golden_rose_runtime, golden_rose_migrator"
        )
        execute(f"GRANT SELECT, INSERT ON TABLE {table} TO golden_rose_runtime")
    execute(
        "GRANT UPDATE(version,label_en,label_es,active,updated_at,updated_"
        "by) ON work_interests TO golden_rose_runtime"
    )
    for function in FUNCTIONS:
        execute(f"ALTER FUNCTION {function}() OWNER TO golden_rose_schema_owner")
        execute(
            f"REVOKE ALL ON FUNCTION {function}() "
            "FROM PUBLIC, golden_rose_runtime, golden_rose_migrator"
        )


INTAKE_FUNCTIONS = """
CREATE OR REPLACE FUNCTION guard_intake_identity() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF TG_TABLE_NAME='intakes' THEN
   IF TG_OP='INSERT' THEN
     IF NEW.version<>1 OR NEW.content_version<>1 OR NEW.created_by<>NEW.updated_by OR
NEW.created_at<>NEW.updated_at THEN
       RAISE EXCEPTION 'invalid intake initial attribution' USING ERRCODE='23514',
CONSTRAINT='ck_intakes_initial_attribution';
     END IF;
   ELSIF
(NEW.intake_id,NEW.kind,NEW.schema_version,NEW.created_at,NEW.created_by,NEW.lifecycle_status)
      IS DISTINCT FROM
(OLD.intake_id,OLD.kind,OLD.schema_version,OLD.created_at,OLD.created_by,OLD.lifecycle_status)
      OR NEW.version<>OLD.version+1 OR NEW.content_version NOT IN
(OLD.content_version,OLD.content_version+1)
      OR (NEW.content_version=OLD.content_version AND NEW.content IS DISTINCT FROM
OLD.content) THEN
     RAISE EXCEPTION 'invalid intake revision' USING
ERRCODE='23514',CONSTRAINT='ck_intakes_revision_identity';
   END IF;
 ELSIF TG_OP='UPDATE' AND (NEW.intake_id,NEW.section) IS DISTINCT FROM
(OLD.intake_id,OLD.section) THEN
   RAISE EXCEPTION 'immutable address identity' USING
ERRCODE='23514',CONSTRAINT='ck_intake_addresses_identity';
 END IF;
 RETURN NEW;
END $$;
CREATE OR REPLACE FUNCTION guard_intake_write_authority() RETURNS trigger LANGUAGE
plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM command_results r JOIN audit_events a
   ON a.command_id=r.command_id AND a.entity_type=r.entity_type AND
a.entity_id=r.entity_id
   WHERE r.entity_type='intake' AND r.entity_id=NEW.intake_id AND
r.result_version=NEW.version
     AND r.actor_id=NEW.updated_by AND a.occurred_at=NEW.updated_at AND
a.xmin::text=pg_current_xact_id()::text
     AND ((TG_OP='INSERT' AND r.command_type='create_intake') OR (TG_OP='UPDATE' AND (
       (r.command_type IN ('revise_intake','revise_intake_address') AND
NEW.content_version=OLD.content_version+1)
       OR (r.command_type IN ('review_intake','follow_up_intake') AND
NEW.content_version=OLD.content_version AND NEW.content=OLD.content))))) THEN
   RAISE EXCEPTION 'missing atomic intake authority' USING
ERRCODE='23514',CONSTRAINT='ck_intakes_atomic_authority';
 END IF;
 RETURN NULL;
END $$;
"""

WORKFLOW_FUNCTION = """
CREATE FUNCTION guard_intake_workflow_authority() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE ev audit_events%ROWTYPE; rev intake_reviews%ROWTYPE; follow
intake_follow_up_events%ROWTYPE;
        parent intakes%ROWTYPE; payload intake_review_payloads%ROWTYPE; expected jsonb;
event uuid;
BEGIN
 IF TG_TABLE_NAME='audit_events' THEN
   IF NEW.event_type NOT IN ('intake.reviewed','intake.follow_up_recorded') THEN RETURN
NULL; END IF;
   event:=NEW.audit_event_id;
 ELSIF TG_TABLE_NAME='intake_review_payloads' THEN
   SELECT event_id INTO event FROM intake_reviews WHERE review_id=NEW.review_id;
 ELSE event:=NEW.event_id;
 END IF;
 SELECT * INTO ev FROM audit_events WHERE audit_event_id=event;
 SELECT * INTO parent FROM intakes WHERE intake_id=ev.entity_id;
 IF ev.audit_event_id IS NULL OR ev.entity_type<>'intake' OR ev.event_type NOT IN
('intake.reviewed','intake.follow_up_recorded')
   OR NOT EXISTS(SELECT 1 FROM audit_events WHERE audit_event_id=event AND
xmin::text=pg_current_xact_id()::text) OR NOT EXISTS(SELECT 1 FROM intakes WHERE
intake_id=parent.intake_id AND xmin::text=pg_current_xact_id()::text)
   OR (parent.version,parent.updated_by,parent.updated_at) IS DISTINCT FROM
(ev.new_record_version,ev.actor_id,ev.occurred_at) THEN
   RAISE EXCEPTION 'invalid workflow authority' USING ERRCODE='23514';
 END IF;
 IF ev.event_type='intake.follow_up_recorded' AND EXISTS(
   SELECT 1 FROM intake_reviews WHERE event_id=event) THEN
   RAISE EXCEPTION 'standalone follow up cannot carry a review' USING ERRCODE='23514';
 END IF;
 IF ev.event_type='intake.reviewed' THEN
   IF NOT EXISTS(SELECT 1 FROM command_results r
     WHERE r.command_id=ev.command_id AND r.command_type='review_intake'
       AND r.entity_type='intake' AND r.entity_id=ev.entity_id
       AND r.result_version=ev.new_record_version AND r.actor_id=ev.actor_id
       AND r.event_type='intake.reviewed') THEN
     RAISE EXCEPTION 'missing exact review command authority' USING ERRCODE='23514';
   END IF;
   SELECT * INTO rev FROM intake_reviews WHERE event_id=event;
   SELECT * INTO payload FROM intake_review_payloads WHERE review_id=rev.review_id;
   SELECT jsonb_build_object('kind',parent.kind,'content',parent.content,'addresses',
COALESCE(jsonb_object_agg(section,jsonb_strip_nulls(to_jsonb(a)-'intake_id'-'section'))
FILTER(WHERE section IS NOT NULL
  AND jsonb_strip_nulls(to_jsonb(a)-'intake_id'-'section')<>'{}'::jsonb),'{}'::jsonb))
     INTO expected FROM intake_addresses a WHERE intake_id=parent.intake_id;
   IF rev.review_id IS NULL OR payload.review_id IS NULL
     OR
(rev.command_id,rev.intake_id,rev.result_version,rev.reviewed_record_version,rev.reviewed_content_version,rev.actor_id,rev.occurred_at)
       IS DISTINCT FROM
(ev.command_id,ev.entity_id,ev.new_record_version,ev.prior_record_version,parent.content_version,ev.actor_id,ev.occurred_at)
     OR payload.reviewed_content IS DISTINCT FROM expected THEN
     RAISE EXCEPTION 'invalid review payload or authority' USING ERRCODE='23514';
   END IF;
   IF rev.outcome='intake_reviewed' THEN
     IF EXISTS(SELECT 1 FROM intake_follow_up_events WHERE event_id=event) THEN RAISE
EXCEPTION 'unexpected follow up' USING ERRCODE='23514'; END IF;
     RETURN NULL;
   END IF;
 END IF;
 SELECT * INTO follow FROM intake_follow_up_events WHERE event_id=event;
 IF follow.event_id IS NULL OR NOT EXISTS(SELECT 1 FROM intake_history_payloads WHERE
event_id=event)
   OR
(follow.command_id,follow.intake_id,follow.version,follow.content_version,follow.actor_id,follow.occurred_at)
    IS DISTINCT FROM
(ev.command_id,ev.entity_id,ev.new_record_version,parent.content_version,ev.actor_id,ev.occurred_at)
   OR (ev.event_type='intake.reviewed' AND (follow.action<>'needs_follow_up' OR
follow.review_id IS DISTINCT FROM rev.review_id OR
follow.actor_display_name<>rev.actor_display_name))
   OR (ev.event_type='intake.follow_up_recorded' AND (follow.action='needs_follow_up' OR
NOT EXISTS(SELECT 1 FROM intake_follow_up_events prior WHERE
prior.intake_id=parent.intake_id AND prior.version<follow.version))) THEN
   RAISE EXCEPTION 'invalid follow up authority' USING ERRCODE='23514';
 END IF;
 RETURN NULL;
END $$;
"""

CATALOG_FUNCTIONS = """
CREATE FUNCTION guard_work_interest_identity() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF TG_OP='INSERT' THEN
   IF NEW.version<>1 OR (NEW.created_at,NEW.created_by) IS DISTINCT FROM
(NEW.updated_at,NEW.updated_by) THEN RAISE EXCEPTION 'invalid catalog creation' USING
ERRCODE='23514'; END IF;
 ELSE
   IF (NEW.interest_id,NEW.code,NEW.created_at,NEW.created_by) IS DISTINCT FROM
(OLD.interest_id,OLD.code,OLD.created_at,OLD.created_by)
      OR NEW.version<>OLD.version+1 OR (NEW.label_en,NEW.label_es,NEW.active) IS NOT
DISTINCT FROM (OLD.label_en,OLD.label_es,OLD.active) THEN
     RAISE EXCEPTION 'invalid catalog revision' USING ERRCODE='23514';
   END IF;
 END IF; RETURN NEW;
END $$;
CREATE FUNCTION guard_work_interest_authority() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE item work_interests%ROWTYPE; hist work_interest_versions%ROWTYPE; target uuid;
supplied_version integer;
BEGIN
 IF TG_TABLE_NAME='audit_events' THEN
   IF NEW.entity_type<>'work_interest' THEN RETURN NULL; END IF;
   target:=NEW.entity_id;
 ELSE target:=NEW.interest_id; supplied_version:=NEW.version; END IF;
 SELECT * INTO item FROM work_interests WHERE interest_id=target;
 SELECT * INTO hist FROM work_interest_versions WHERE interest_id=target AND
version=item.version;
 IF TG_TABLE_NAME='audit_events' THEN
   IF (NEW.command_id,NEW.new_record_version,NEW.actor_id,NEW.occurred_at)
      IS DISTINCT FROM (hist.command_id,item.version,item.updated_by,item.updated_at) THEN
     RAISE EXCEPTION 'catalog audit lacks exact domain version' USING ERRCODE='23514';
   END IF;
 END IF;
 IF item.interest_id IS NULL OR hist.interest_id IS NULL OR NOT EXISTS(SELECT 1 FROM
work_interests WHERE interest_id=target AND xmin::text=pg_current_xact_id()::text)
   OR NOT EXISTS(SELECT 1 FROM work_interest_versions WHERE interest_id=target AND
version=item.version AND xmin::text=pg_current_xact_id()::text)
   OR (hist.label_en,hist.label_es,hist.active,hist.actor_id,hist.occurred_at) IS
DISTINCT FROM (item.label_en,item.label_es,item.active,item.updated_by,item.updated_at)
   OR (supplied_version IS NOT NULL AND supplied_version<>item.version)
   OR NOT EXISTS(SELECT 1 FROM command_results r JOIN audit_events a ON
a.command_id=r.command_id AND a.entity_type=r.entity_type AND a.entity_id=r.entity_id
     WHERE r.command_id=hist.command_id AND r.entity_type='work_interest' AND
r.entity_id=target
       AND r.result_version=item.version AND r.actor_id=item.updated_by AND
a.occurred_at=item.updated_at
       AND a.xmin::text=pg_current_xact_id()::text
       AND r.command_type=CASE WHEN item.version=1 THEN 'create_work_interest' ELSE
'revise_work_interest' END) THEN
   RAISE EXCEPTION 'missing atomic catalog authority' USING ERRCODE='23514';
 END IF; RETURN NULL;
END $$;
"""


def downgrade() -> None:
    execute(
        "LOCK TABLE "
        + ",".join(TABLES)
        + (
            ", intakes, audit_events, command_results, command_receipts, entit"
            "y_authorities IN SHARE ROW EXCLUSIVE MODE"
        )
    )
    data = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT "
                + " OR ".join(f"EXISTS(SELECT 1 FROM {t})" for t in TABLES)
                + (
                    " OR EXISTS(SELECT 1 FROM command_receipts WHERE command_type IN ("
                    "'review_intake','follow_up_intake','create_work_interest','revise"
                    "_work_interest'))"
                )
            )
        )
        .scalar_one()
    )
    if data:
        raise RuntimeError("successor review/follow-up/catalog data blocks downgrade before DDL")
    execute("SET CONSTRAINTS ALL IMMEDIATE")
    for function in FUNCTIONS:
        for table in ("audit_events", *TABLES):
            execute(f"DROP TRIGGER IF EXISTS {function} ON {table}")
    shapes(False)
    op.drop_column("entity_authorities", "work_interest_id")
    execute("ALTER TABLE intake_reviews DROP CONSTRAINT fk_intake_reviews_required_payload")
    execute(
        "ALTER TABLE intake_follow_up_events DROP CONSTRAINT fk_intake_follow_up_required_payload"
    )
    for table in reversed(TABLES):
        op.drop_table(table)
    for function in FUNCTIONS:
        execute(f"DROP FUNCTION {function}()")
    check("intakes", "ck_intakes_content_version", "content_version>=1 AND content_version=version")
    execute(PREDECESSOR_INTAKE_FUNCTIONS)


PREDECESSOR_INTAKE_FUNCTIONS = """
    CREATE OR REPLACE FUNCTION guard_intake_identity() RETURNS trigger LANGUAGE plpgsql
    SET search_path = pg_catalog, public, pg_temp AS $$
    BEGIN
      IF TG_TABLE_NAME='intakes' THEN
        IF TG_OP='INSERT' THEN
          IF NEW.version<>1 OR NEW.created_by<>NEW.updated_by OR
NEW.created_at<>NEW.updated_at THEN
            RAISE EXCEPTION 'invalid intake initial attribution' USING ERRCODE='23514',
            CONSTRAINT='ck_intakes_initial_attribution';
          END IF;
        ELSIF (NEW.intake_id,NEW.kind,NEW.schema_version,NEW.created_at,NEW.created_by,
        NEW.lifecycle_status)
          IS DISTINCT FROM (OLD.intake_id,OLD.kind,OLD.schema_version,OLD.created_at,
          OLD.created_by,OLD.lifecycle_status)
          OR NEW.version<>OLD.version+1 OR NEW.content_version<>OLD.content_version+1
THEN
          RAISE EXCEPTION 'invalid intake revision' USING ERRCODE='23514',
          CONSTRAINT='ck_intakes_revision_identity';
        END IF;
      ELSIF TG_OP='UPDATE' AND (NEW.intake_id,NEW.section) IS DISTINCT FROM
(OLD.intake_id,
      OLD.section) THEN
        RAISE EXCEPTION 'immutable address identity' USING ERRCODE='23514',
        CONSTRAINT='ck_intake_addresses_identity';
      END IF;
      RETURN NEW;
    END $$;



    CREATE OR REPLACE FUNCTION guard_intake_write_authority() RETURNS trigger LANGUAGE
plpgsql
    SET search_path = pg_catalog, public, pg_temp AS $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM command_results r JOIN audit_events a
        ON a.command_id=r.command_id AND a.entity_type=r.entity_type AND
a.entity_id=r.entity_id
        WHERE r.entity_type='intake' AND r.entity_id=NEW.intake_id
        AND r.result_version=NEW.version AND r.actor_id=NEW.updated_by
        AND a.occurred_at=NEW.updated_at AND a.xmin::text=pg_current_xact_id()::text
        AND ((TG_OP='INSERT' AND r.command_type='create_intake')
          OR (TG_OP='UPDATE' AND r.command_type IN
('revise_intake','revise_intake_address')))) THEN
        RAISE EXCEPTION 'missing atomic intake authority' USING ERRCODE='23514',
        CONSTRAINT='ck_intakes_atomic_authority';
      END IF;
      RETURN NULL;
    END $$;


"""
