from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKeyConstraint,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import BYTEA, JSONB, TIMESTAMP, UUID

metadata = MetaData()

employers = Table(
    "employers",
    metadata,
    Column("employer_id", UUID(as_uuid=True), primary_key=True),
    Column("employer_type", String(length=32), nullable=False),
    Column("display_name", String(length=200), nullable=False),
    Column("lifecycle_status", String(length=32), nullable=False),
    Column("source_channel", String(length=32), nullable=False),
    Column("received_at", TIMESTAMP(timezone=True), nullable=False),
    Column("created_at", TIMESTAMP(timezone=True), nullable=False),
    Column("created_by", UUID(as_uuid=True), nullable=False),
    Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
    Column("updated_by", UUID(as_uuid=True), nullable=False),
    Column("version", Integer, nullable=False),
    CheckConstraint("employer_type IN ('household', 'business')", name="ck_employers_type"),
    CheckConstraint("btrim(display_name) <> ''", name="ck_employers_display_name_nonblank"),
    CheckConstraint("lifecycle_status = 'draft'", name="ck_employers_lifecycle_status_draft"),
    CheckConstraint(
        "source_channel = 'staff_entry'", name="ck_employers_source_channel_staff_entry"
    ),
    CheckConstraint("version >= 1", name="ck_employers_version_positive"),
)

employer_contacts = Table(
    "employer_contacts",
    metadata,
    Column("employer_contact_id", UUID(as_uuid=True), primary_key=True),
    Column("employer_id", UUID(as_uuid=True), nullable=False),
    Column("full_name", String(length=200), nullable=False),
    Column("created_at", TIMESTAMP(timezone=True), nullable=False),
    Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
    Column("created_by", UUID(as_uuid=True), nullable=False),
    Column("updated_by", UUID(as_uuid=True), nullable=False),
    Column("version", Integer, nullable=False),
    ForeignKeyConstraint(
        ["employer_id"],
        ["employers.employer_id"],
        name="fk_employer_contacts_employer",
    ),
    UniqueConstraint(
        "employer_id",
        "employer_contact_id",
        name="uq_employer_contacts_parent_scoped_identity",
    ),
    CheckConstraint("btrim(full_name) <> ''", name="ck_employer_contacts_full_name_nonblank"),
    CheckConstraint("version = 1", name="ck_employer_contacts_version_is_one"),
)

entity_authorities = Table(
    "entity_authorities",
    metadata,
    Column("entity_type", String(length=32), primary_key=True),
    Column("entity_id", UUID(as_uuid=True), primary_key=True),
    Column("employer_id", UUID(as_uuid=True), nullable=True),
    Column("employer_contact_id", UUID(as_uuid=True), nullable=True),
    ForeignKeyConstraint(
        ["employer_id"],
        ["employers.employer_id"],
        name="fk_entity_authorities_employer",
        deferrable=True,
        initially="DEFERRED",
    ),
    ForeignKeyConstraint(
        ["employer_contact_id"],
        ["employer_contacts.employer_contact_id"],
        name="fk_entity_authorities_employer_contact",
        deferrable=True,
        initially="DEFERRED",
    ),
    UniqueConstraint("employer_id", name="uq_entity_authorities_employer_id"),
    UniqueConstraint("employer_contact_id", name="uq_entity_authorities_employer_contact_id"),
    CheckConstraint(
        "entity_type IN ('employer', 'employer_contact')",
        name="ck_entity_authorities_entity_type",
    ),
    CheckConstraint(
        "((entity_type = 'employer' AND employer_id = entity_id "
        "AND employer_contact_id IS NULL) OR "
        "(entity_type = 'employer_contact' "
        "AND employer_contact_id = entity_id AND employer_id IS NULL))",
        name="ck_entity_authorities_exactly_one_concrete_id",
    ),
)

command_receipts = Table(
    "command_receipts",
    metadata,
    Column("command_id", UUID(as_uuid=True), primary_key=True),
    Column("command_schema_version", Integer, nullable=False),
    Column("command_type", String(length=64), nullable=False),
    Column("actor_id", UUID(as_uuid=True), nullable=False),
    Column("request_fingerprint", BYTEA, nullable=False),
    Column("result_entity_type", String(length=32), nullable=False),
    Column("result_entity_id", UUID(as_uuid=True), nullable=False),
    Column("result_record_version", Integer, nullable=False),
    Column("result_event_type", String(length=64), nullable=False),
    Column("created_at", TIMESTAMP(timezone=True), nullable=False),
    CheckConstraint("command_schema_version = 1", name="ck_command_receipts_schema_version"),
    CheckConstraint(
        "command_type IN ("
        "'create_draft_employer', 'create_employer_contact', 'revise_draft_employer'"
        ")",
        name="ck_command_receipts_command_type",
    ),
    CheckConstraint(
        "octet_length(request_fingerprint) = 32", name="ck_command_receipts_request_fingerprint_len"
    ),
    CheckConstraint(
        "result_entity_type IN ('employer', 'employer_contact')",
        name="ck_command_receipts_entity_type",
    ),
    CheckConstraint(
        "result_record_version >= 1", name="ck_command_receipts_result_record_version_positive"
    ),
    CheckConstraint(
        "((command_type = 'create_draft_employer' "
        "AND result_entity_type = 'employer' "
        "AND result_event_type = 'employer.created' "
        "AND result_record_version = 1) OR "
        "(command_type = 'create_employer_contact' "
        "AND result_entity_type = 'employer_contact' "
        "AND result_event_type = 'employer_contact.created' "
        "AND result_record_version = 1) OR "
        "(command_type = 'revise_draft_employer' "
        "AND result_entity_type = 'employer' "
        "AND result_event_type = 'employer.draft_revised' "
        "AND result_record_version >= 2))",
        name="ck_command_receipts_result_authority_shape",
    ),
    ForeignKeyConstraint(
        ["result_entity_type", "result_entity_id"],
        ["entity_authorities.entity_type", "entity_authorities.entity_id"],
        name="fk_command_receipts_result_entity_authority",
        deferrable=True,
        initially="DEFERRED",
    ),
    ForeignKeyConstraint(
        ["command_id", "result_entity_type", "result_entity_id"],
        ["audit_events.command_id", "audit_events.entity_type", "audit_events.entity_id"],
        name="fk_command_receipts_creation_event",
        deferrable=True,
        initially="DEFERRED",
    ),
    ForeignKeyConstraint(
        [
            "command_id",
            "result_entity_id",
            "result_record_version",
            "result_event_type",
            "actor_id",
        ],
        [
            "audit_events.command_id",
            "audit_events.entity_id",
            "audit_events.new_record_version",
            "audit_events.event_type",
            "audit_events.actor_id",
        ],
        name="fk_command_receipts_result_audit_event",
        deferrable=True,
        initially="DEFERRED",
    ),
    UniqueConstraint("command_id", "result_entity_id", name="uq_command_receipts_command_result"),
    UniqueConstraint(
        "command_id",
        "result_entity_type",
        "result_entity_id",
        name="uq_command_receipts_command_result_entity",
    ),
    UniqueConstraint(
        "command_id",
        "result_entity_type",
        "result_entity_id",
        "result_record_version",
        "result_event_type",
        "actor_id",
        name="uq_command_receipts_result_authority",
    ),
)

audit_events = Table(
    "audit_events",
    metadata,
    Column("audit_event_id", UUID(as_uuid=True), primary_key=True),
    Column("event_schema_name", String(length=64), nullable=False),
    Column("event_schema_version", Integer, nullable=False),
    Column("event_type", String(length=64), nullable=False),
    Column("entity_type", String(length=32), nullable=False),
    Column("entity_id", UUID(as_uuid=True), nullable=False),
    Column("entity_sequence", Integer, nullable=False),
    Column("prior_record_version", Integer, nullable=False),
    Column("new_record_version", Integer, nullable=False),
    Column("actor_type", String(length=32), nullable=False),
    Column("actor_id", UUID(as_uuid=True), nullable=False),
    Column("initiating_staff_actor_id", UUID(as_uuid=True), nullable=True),
    Column("occurred_at", TIMESTAMP(timezone=True), nullable=False),
    Column("effective_at", TIMESTAMP(timezone=True), nullable=True),
    Column("command_id", UUID(as_uuid=True), nullable=False),
    Column("correlation_id", UUID(as_uuid=True), nullable=False),
    Column("reason_code", String(length=64), nullable=True),
    Column("reason_text", String(length=512), nullable=True),
    Column("source_type", String(length=32), nullable=False),
    Column("source_reference", String(length=255), nullable=True),
    Column("related_event_ids", JSONB, nullable=False),
    Column("changed_fields", JSONB, nullable=False),
    Column("payload_classification", String(length=64), nullable=False),
    UniqueConstraint(
        "entity_type", "entity_id", "entity_sequence", name="uq_audit_events_entity_sequence"
    ),
    UniqueConstraint(
        "command_id", "entity_type", "entity_id", name="uq_audit_events_command_entity"
    ),
    UniqueConstraint("command_id", "event_type", name="uq_audit_events_command_event_type"),
    UniqueConstraint(
        "command_id",
        "entity_id",
        "new_record_version",
        "event_type",
        "actor_id",
        name="uq_audit_events_result_authority",
    ),
    CheckConstraint(
        "event_schema_name IN ("
        "'employer.created', 'employer_contact.created', 'employer.draft_revised'"
        ")",
        name="ck_audit_events_schema_name",
    ),
    CheckConstraint("event_schema_name = event_type", name="ck_audit_events_schema_matches_type"),
    CheckConstraint("event_schema_version = 1", name="ck_audit_events_schema_version"),
    CheckConstraint(
        "event_type IN ('employer.created', 'employer_contact.created', 'employer.draft_revised')",
        name="ck_audit_events_event_type",
    ),
    CheckConstraint(
        "entity_type IN ('employer', 'employer_contact')", name="ck_audit_events_entity_type"
    ),
    CheckConstraint("actor_type = 'staff'", name="ck_audit_events_actor_type"),
    CheckConstraint(
        "correlation_id = command_id", name="ck_audit_events_correlation_matches_command"
    ),
    CheckConstraint("source_type = 'staff_api'", name="ck_audit_events_source_type"),
    CheckConstraint(
        "payload_classification = 'sensitive_operational'",
        name="ck_audit_events_payload_classification",
    ),
    CheckConstraint(
        "entity_sequence = new_record_version",
        name="ck_audit_events_entity_sequence_matches_new_record_version",
    ),
    CheckConstraint(
        "new_record_version = prior_record_version + 1",
        name="ck_audit_events_one_step_version_advance",
    ),
    ForeignKeyConstraint(
        ["entity_type", "entity_id"],
        ["entity_authorities.entity_type", "entity_authorities.entity_id"],
        name="fk_audit_events_entity_authority",
        deferrable=True,
        initially="DEFERRED",
    ),
    ForeignKeyConstraint(
        ["command_id", "entity_type", "entity_id", "new_record_version", "event_type", "actor_id"],
        [
            "command_receipts.command_id",
            "command_receipts.result_entity_type",
            "command_receipts.result_entity_id",
            "command_receipts.result_record_version",
            "command_receipts.result_event_type",
            "command_receipts.actor_id",
        ],
        name="fk_audit_events_command_result",
        deferrable=True,
        initially="DEFERRED",
    ),
)
