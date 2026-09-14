"""Durable staff intake drafts and exact command result authority.

Revision ID: 0006_intake_drafts
Revises: 0005_database_authority
"""

import sqlalchemy as sa
from alembic import op

revision = "0006_intake_drafts"
down_revision = "0005_database_authority"
branch_labels = None
depends_on = None

LEGACY_SHAPE = """((command_type='create_draft_employer' AND result_entity_type='employer'
 AND result_event_type='employer.created' AND result_record_version=1)
 OR (command_type='create_employer_contact' AND result_entity_type='employer_contact'
 AND result_event_type='employer_contact.created' AND result_record_version=1)
 OR (command_type='revise_draft_employer' AND result_entity_type='employer'
 AND result_event_type='employer.draft_revised' AND result_record_version>=2))"""
INTAKE_SHAPE = """((command_type='create_intake' AND result_entity_type='intake'
 AND result_event_type='intake.created' AND result_record_version=1)
 OR (command_type IN ('revise_intake','revise_intake_address') AND result_entity_type='intake'
 AND result_event_type='intake.revised' AND result_record_version>=2))"""
LEGACY_COMMANDS = "'create_draft_employer','create_employer_contact','revise_draft_employer'"
LEGACY_EVENTS = "'employer.created','employer_contact.created','employer.draft_revised'"
LEGACY_TYPES = "'employer','employer_contact'"
NEW_TABLES = ("intakes", "intake_addresses", "intake_links", "command_results")
FUNCTIONS = (
    "populate_legacy_command_result",
    "guard_intake_identity",
    "guard_intake_write_authority",
    "guard_intake_address_authority",
)


def execute(sql: str) -> None:
    op.execute(sa.text(sql))


def replace_check(table: str, name: str, expression: str) -> None:
    op.drop_constraint(name, table, type_="check")
    op.create_check_constraint(name, table, expression)


def receipt_checks(successor: bool) -> None:
    types = LEGACY_TYPES + (",'intake'" if successor else "")
    commands = LEGACY_COMMANDS + (
        ",'create_intake','revise_intake','revise_intake_address'" if successor else ""
    )
    events = LEGACY_EVENTS + (",'intake.created','intake.revised'" if successor else "")
    replace_check(
        "command_receipts", "ck_command_receipts_command_type", f"command_type IN ({commands})"
    )
    replace_check(
        "command_receipts", "ck_command_receipts_entity_type", f"result_entity_type IN ({types})"
    )
    replace_check(
        "command_receipts",
        "ck_command_receipts_result_authority_shape",
        f"({LEGACY_SHAPE} OR {INTAKE_SHAPE})" if successor else LEGACY_SHAPE,
    )
    for column, name in [
        ("event_type", "ck_audit_events_event_type"),
        ("event_schema_name", "ck_audit_events_schema_name"),
    ]:
        replace_check("audit_events", name, f"{column} IN ({events})")
    replace_check("audit_events", "ck_audit_events_entity_type", f"entity_type IN ({types})")


def upgrade() -> None:
    execute(
        "LOCK TABLE command_receipts, audit_events, entity_authorities IN SHARE ROW EXCLUSIVE MODE"
    )
    execute("""
    CREATE TABLE intakes (
      intake_id uuid PRIMARY KEY, kind varchar(32) NOT NULL,
      schema_version integer NOT NULL, content jsonb NOT NULL,
      lifecycle_status varchar(32) NOT NULL,
      version integer NOT NULL, content_version integer NOT NULL,
      created_at timestamptz NOT NULL, created_by uuid NOT NULL,
      updated_at timestamptz NOT NULL, updated_by uuid NOT NULL,
      CONSTRAINT ck_intakes_kind CHECK (kind IN ('worker','employer')),
      CONSTRAINT ck_intakes_schema_version CHECK (schema_version=1),
      CONSTRAINT ck_intakes_lifecycle_draft CHECK (lifecycle_status='draft'),
      CONSTRAINT ck_intakes_version_positive CHECK (version>=1),
      CONSTRAINT ck_intakes_content_version CHECK (content_version>=1 AND content_version=version),
      CONSTRAINT ck_intakes_content_object CHECK (jsonb_typeof(content)='object'),
      CONSTRAINT ck_intakes_content_size CHECK (octet_length(content::text)<=32768),
      CONSTRAINT ck_intakes_content_kind CHECK (
        (kind='worker' AND content - ARRAY['full_name','phone','interests',
        'availability']::text[]='{}'::jsonb)
        OR (kind='employer' AND content - ARRAY['employer_type','display_name',
        'representative_name',
          'phone','role_title','duties_summary','worker_count','schedule',
          'offer']::text[]='{}'::jsonb)),
      CONSTRAINT uq_intakes_id_kind UNIQUE (intake_id,kind)
    );
    CREATE TABLE intake_addresses (
      intake_id uuid NOT NULL, section varchar(32) NOT NULL,
      line1 varchar(200), line2 varchar(200), locality varchar(100), region varchar(100),
      postal_code varchar(32), country varchar(2),
      PRIMARY KEY (intake_id,section),
      CONSTRAINT fk_intake_addresses_intake FOREIGN KEY (intake_id) REFERENCES intakes(intake_id),
      CONSTRAINT ck_intake_addresses_section CHECK
        (section IN ('worker_residence','party_address','worksite_address')),
      CONSTRAINT ck_intake_addresses_nonblank CHECK
        ((line1 IS NULL OR btrim(line1)<>'') AND (line2 IS NULL OR btrim(line2)<>'')
        AND (locality IS NULL OR btrim(locality)<>'') AND (region IS NULL OR btrim(region)<>'')
        AND (postal_code IS NULL OR btrim(postal_code)<>'')),
      CONSTRAINT ck_intake_addresses_country CHECK (country IS NULL OR country ~ '^[A-Z]{2}$')
    );
    CREATE TABLE intake_links (
      intake_id uuid PRIMARY KEY,
      CONSTRAINT fk_intake_links_intake FOREIGN KEY (intake_id) REFERENCES intakes(intake_id),
      CONSTRAINT ck_intake_links_not_available CHECK (false)
    );
    ALTER TABLE entity_authorities ADD COLUMN intake_id uuid;
    ALTER TABLE entity_authorities ADD CONSTRAINT fk_entity_authorities_intake
      FOREIGN KEY (intake_id) REFERENCES intakes(intake_id) DEFERRABLE INITIALLY DEFERRED;
    ALTER TABLE entity_authorities ADD CONSTRAINT uq_entity_authorities_intake_id UNIQUE(intake_id);
    """)
    replace_check(
        "entity_authorities",
        "ck_entity_authorities_entity_type",
        "entity_type IN ('employer','employer_contact','intake')",
    )
    replace_check(
        "entity_authorities",
        "ck_entity_authorities_exactly_one_concrete_id",
        """
       (entity_type='employer' AND employer_id IS NOT NULL AND employer_id=entity_id
        AND employer_contact_id IS NULL AND intake_id IS NULL)
       OR (entity_type='employer_contact' AND employer_contact_id IS NOT NULL
        AND employer_contact_id=entity_id AND employer_id IS NULL AND intake_id IS NULL)
       OR (entity_type='intake' AND intake_id IS NOT NULL AND intake_id=entity_id
        AND employer_id IS NULL AND employer_contact_id IS NULL)
    """,
    )
    receipt_checks(True)
    execute("""
    ALTER TABLE command_receipts ADD CONSTRAINT uq_command_receipts_actor_command
      UNIQUE(command_id,actor_id,command_type);
    CREATE TABLE command_results (
      command_id uuid NOT NULL, entity_type varchar(32) NOT NULL, entity_id uuid NOT NULL,
      result_version integer NOT NULL, event_type varchar(64) NOT NULL,
      actor_id uuid NOT NULL, command_type varchar(64) NOT NULL,
      PRIMARY KEY(command_id,entity_type,entity_id),
      CONSTRAINT uq_command_results_single_result UNIQUE(command_id),
      CONSTRAINT uq_command_results_exact_authority
        UNIQUE(command_id,entity_type,entity_id,result_version,event_type,actor_id),
      CONSTRAINT ck_command_results_version_positive CHECK(result_version>=1),
      CONSTRAINT fk_command_results_entity_authority FOREIGN KEY(entity_type,entity_id)
        REFERENCES entity_authorities(entity_type,entity_id) DEFERRABLE INITIALLY DEFERRED,
      CONSTRAINT fk_command_results_receipt_actor_type FOREIGN KEY(command_id,actor_id,command_type)
        REFERENCES command_receipts(command_id,actor_id,command_type) DEFERRABLE INITIALLY DEFERRED,
      CONSTRAINT fk_command_results_exact_audit FOREIGN KEY(command_id,entity_id,
      result_version,event_type,actor_id)
        REFERENCES audit_events(command_id,entity_id,new_record_version,event_type,actor_id)
        DEFERRABLE INITIALLY DEFERRED,
      CONSTRAINT fk_command_results_typed_audit FOREIGN KEY(command_id,entity_type,entity_id)
        REFERENCES audit_events(command_id,entity_type,entity_id) DEFERRABLE INITIALLY DEFERRED
    );
    INSERT INTO command_results(command_id,entity_type,entity_id,result_version,event_type,
    actor_id,command_type)
      SELECT command_id,result_entity_type,result_entity_id,result_record_version,
      result_event_type,actor_id,command_type
      FROM command_receipts;
    SET CONSTRAINTS ALL IMMEDIATE;
    SET CONSTRAINTS ALL DEFERRED;
    ALTER TABLE audit_events DROP CONSTRAINT fk_audit_events_command_result;
    ALTER TABLE audit_events ADD CONSTRAINT fk_audit_events_command_result
      FOREIGN KEY(command_id,entity_type,entity_id,new_record_version,event_type,actor_id)
      REFERENCES command_results(command_id,entity_type,entity_id,result_version,event_type,
      actor_id)
      DEFERRABLE INITIALLY DEFERRED;
    ALTER TABLE command_receipts ADD CONSTRAINT fk_command_receipts_primary_result
      FOREIGN KEY(command_id,result_entity_type,result_entity_id,result_record_version,
      result_event_type,actor_id)
      REFERENCES command_results(command_id,entity_type,entity_id,result_version,event_type,
      actor_id)
      DEFERRABLE INITIALLY DEFERRED;
    """)
    result_shape = f"({LEGACY_SHAPE} OR {INTAKE_SHAPE})"
    result_shape = (
        result_shape.replace("result_entity_type", "entity_type")
        .replace("result_event_type", "event_type")
        .replace("result_record_version", "result_version")
    )
    op.create_check_constraint(
        "ck_command_results_authority_shape", "command_results", result_shape
    )
    execute("""
    CREATE FUNCTION populate_legacy_command_result() RETURNS trigger LANGUAGE plpgsql
    SET search_path = pg_catalog, public, pg_temp AS $$
    BEGIN
      IF NEW.command_type IN ('create_draft_employer','create_employer_contact',
      'revise_draft_employer') THEN
        INSERT INTO command_results VALUES (NEW.command_id,NEW.result_entity_type,
        NEW.result_entity_id,
          NEW.result_record_version,NEW.result_event_type,NEW.actor_id,NEW.command_type);
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER populate_legacy_command_result AFTER INSERT ON command_receipts
      FOR EACH ROW EXECUTE FUNCTION populate_legacy_command_result();

    CREATE FUNCTION guard_intake_identity() RETURNS trigger LANGUAGE plpgsql
    SET search_path = pg_catalog, public, pg_temp AS $$
    BEGIN
      IF TG_TABLE_NAME='intakes' THEN
        IF TG_OP='INSERT' THEN
          IF NEW.version<>1 OR NEW.created_by<>NEW.updated_by OR NEW.created_at<>NEW.updated_at THEN
            RAISE EXCEPTION 'invalid intake initial attribution' USING ERRCODE='23514',
            CONSTRAINT='ck_intakes_initial_attribution';
          END IF;
        ELSIF (NEW.intake_id,NEW.kind,NEW.schema_version,NEW.created_at,NEW.created_by,
        NEW.lifecycle_status)
          IS DISTINCT FROM (OLD.intake_id,OLD.kind,OLD.schema_version,OLD.created_at,
          OLD.created_by,OLD.lifecycle_status)
          OR NEW.version<>OLD.version+1 OR NEW.content_version<>OLD.content_version+1 THEN
          RAISE EXCEPTION 'invalid intake revision' USING ERRCODE='23514',
          CONSTRAINT='ck_intakes_revision_identity';
        END IF;
      ELSIF TG_OP='UPDATE' AND (NEW.intake_id,NEW.section) IS DISTINCT FROM (OLD.intake_id,
      OLD.section) THEN
        RAISE EXCEPTION 'immutable address identity' USING ERRCODE='23514',
        CONSTRAINT='ck_intake_addresses_identity';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER guard_intake_identity BEFORE INSERT OR UPDATE ON intakes
      FOR EACH ROW EXECUTE FUNCTION guard_intake_identity();
    CREATE TRIGGER guard_intake_address_identity BEFORE UPDATE ON intake_addresses
      FOR EACH ROW EXECUTE FUNCTION guard_intake_identity();

    CREATE FUNCTION guard_intake_write_authority() RETURNS trigger LANGUAGE plpgsql
    SET search_path = pg_catalog, public, pg_temp AS $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM command_results r JOIN audit_events a
        ON a.command_id=r.command_id AND a.entity_type=r.entity_type AND a.entity_id=r.entity_id
        WHERE r.entity_type='intake' AND r.entity_id=NEW.intake_id
        AND r.result_version=NEW.version AND r.actor_id=NEW.updated_by
        AND a.occurred_at=NEW.updated_at AND a.xmin::text=pg_current_xact_id()::text
        AND ((TG_OP='INSERT' AND r.command_type='create_intake')
          OR (TG_OP='UPDATE' AND r.command_type IN ('revise_intake','revise_intake_address')))) THEN
        RAISE EXCEPTION 'missing atomic intake authority' USING ERRCODE='23514',
        CONSTRAINT='ck_intakes_atomic_authority';
      END IF;
      RETURN NULL;
    END $$;
    CREATE CONSTRAINT TRIGGER guard_intake_write_authority AFTER INSERT OR UPDATE ON intakes
      DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION guard_intake_write_authority();

    CREATE FUNCTION guard_intake_address_authority() RETURNS trigger LANGUAGE plpgsql
    SET search_path = pg_catalog, public, pg_temp AS $$
    DECLARE parent intakes%ROWTYPE;
    BEGIN
      SELECT * INTO parent FROM intakes WHERE intake_id=NEW.intake_id;
      IF (parent.kind='worker') IS DISTINCT FROM (NEW.section='worker_residence') THEN
        RAISE EXCEPTION 'address kind mismatch' USING ERRCODE='23514',
        CONSTRAINT='ck_intake_addresses_kind';
      END IF;
      IF NOT EXISTS (SELECT 1 FROM intakes i JOIN command_results r
        ON r.entity_type='intake' AND r.entity_id=i.intake_id AND r.result_version=i.version
        WHERE i.intake_id=NEW.intake_id AND i.xmin::text=pg_current_xact_id()::text
        AND r.command_type IN ('create_intake','revise_intake_address')
        AND r.actor_id=i.updated_by) THEN
        RAISE EXCEPTION 'missing atomic address authority' USING ERRCODE='23514',
        CONSTRAINT='ck_intake_addresses_atomic_authority';
      END IF;
      RETURN NULL;
    END $$;
    CREATE CONSTRAINT TRIGGER guard_intake_address_authority AFTER INSERT OR UPDATE ON
    intake_addresses
      DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION guard_intake_address_authority();
    """)
    for table in NEW_TABLES:
        operations = (
            "UPDATE OR DELETE OR TRUNCATE"
            if table in ("command_results", "intake_links")
            else "DELETE OR TRUNCATE"
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
        "GRANT UPDATE(content,version,content_version,updated_at,updated_by) ON inta"
        "kes TO golden_rose_runtime"
    )
    execute(
        "GRANT UPDATE(line1,line2,locality,region,postal_code,country) ON intake_add"
        "resses TO golden_rose_runtime"
    )
    for function in FUNCTIONS:
        execute(f"ALTER FUNCTION {function}() OWNER TO golden_rose_schema_owner")
        execute(
            f"REVOKE ALL ON FUNCTION {function}() "
            "FROM PUBLIC, golden_rose_runtime, golden_rose_migrator"
        )


def downgrade() -> None:
    execute(
        "LOCK TABLE intakes, intake_addresses, intake_links, command_results, "
        "command_receipts, audit_events, entity_authorities IN SHARE ROW EXCLUSIVE MODE"
    )
    successor = (
        op.get_bind()
        .execute(
            sa.text("""
      SELECT EXISTS(SELECT 1 FROM intakes) OR EXISTS(SELECT 1 FROM intake_addresses)
        OR EXISTS(SELECT 1 FROM intake_links)
        OR EXISTS(SELECT 1 FROM entity_authorities WHERE entity_type='intake')
        OR EXISTS(SELECT 1 FROM command_results WHERE entity_type='intake')
        OR EXISTS(SELECT 1 FROM command_receipts WHERE result_entity_type='intake')
        OR EXISTS(SELECT 1 FROM audit_events WHERE entity_type='intake')
    """)
        )
        .scalar_one()
    )
    if successor:
        raise RuntimeError("successor intake data blocks downgrade before DDL")
    execute("SET CONSTRAINTS ALL IMMEDIATE")
    execute("DROP TRIGGER populate_legacy_command_result ON command_receipts")
    op.drop_constraint("fk_command_receipts_primary_result", "command_receipts", type_="foreignkey")
    op.drop_constraint("fk_audit_events_command_result", "audit_events", type_="foreignkey")
    execute("""ALTER TABLE audit_events ADD CONSTRAINT fk_audit_events_command_result
      FOREIGN KEY(command_id,entity_type,entity_id,new_record_version,event_type,actor_id)
      REFERENCES command_receipts(command_id,result_entity_type,result_entity_id,
      result_record_version,result_event_type,actor_id)
      DEFERRABLE INITIALLY DEFERRED""")
    op.drop_table("command_results")
    op.drop_constraint("uq_command_receipts_actor_command", "command_receipts", type_="unique")
    receipt_checks(False)
    replace_check(
        "entity_authorities",
        "ck_entity_authorities_entity_type",
        "entity_type IN ('employer','employer_contact')",
    )
    replace_check(
        "entity_authorities",
        "ck_entity_authorities_exactly_one_concrete_id",
        """
      (entity_type='employer' AND employer_id=entity_id AND employer_contact_id IS NULL)
      OR (entity_type='employer_contact' AND employer_contact_id=entity_id AND employer_id IS NULL)
    """,
    )
    op.drop_column("entity_authorities", "intake_id")
    for table in ("intake_links", "intake_addresses", "intakes"):
        op.drop_table(table)
    for function in FUNCTIONS:
        execute(f"DROP FUNCTION {function}()")
