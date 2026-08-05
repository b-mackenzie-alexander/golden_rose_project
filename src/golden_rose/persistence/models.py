from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
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
    Column("version", Integer, nullable=False),
    CheckConstraint("employer_type IN ('household', 'business')", name="ck_employers_type"),
    CheckConstraint("btrim(display_name) <> ''", name="ck_employers_display_name_nonblank"),
    CheckConstraint("lifecycle_status = 'draft'", name="ck_employers_lifecycle_status_draft"),
    CheckConstraint(
        "source_channel = 'staff_entry'", name="ck_employers_source_channel_staff_entry"
    ),
    CheckConstraint("version >= 1", name="ck_employers_version_positive"),
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
    Column("created_at", TIMESTAMP(timezone=True), nullable=False),
    CheckConstraint("command_schema_version = 1", name="ck_command_receipts_schema_version"),
    CheckConstraint(
        "command_type = 'create_draft_employer'", name="ck_command_receipts_command_type"
    ),
    CheckConstraint(
        "octet_length(request_fingerprint) = 32", name="ck_command_receipts_request_fingerprint_len"
    ),
    CheckConstraint("result_entity_type = 'employer'", name="ck_command_receipts_entity_type"),
)

audit_events = Table(
    "audit_events",
    metadata,
    Column("audit_event_id", UUID(as_uuid=True), primary_key=True),
    Column("event_schema_name", String(length=64), nullable=False),
    Column("event_schema_version", Integer, nullable=False),
    Column("event_type", String(length=64), nullable=False),
    Column("entity_type", String(length=32), nullable=False),
    Column("entity_id", UUID(as_uuid=True), ForeignKey("employers.employer_id"), nullable=False),
    Column("entity_sequence", Integer, nullable=False),
    Column("prior_record_version", Integer, nullable=False),
    Column("new_record_version", Integer, nullable=False),
    Column("actor_type", String(length=32), nullable=False),
    Column("actor_id", UUID(as_uuid=True), nullable=False),
    Column("initiating_staff_actor_id", UUID(as_uuid=True), nullable=True),
    Column("occurred_at", TIMESTAMP(timezone=True), nullable=False),
    Column("effective_at", TIMESTAMP(timezone=True), nullable=True),
    Column(
        "command_id", UUID(as_uuid=True), ForeignKey("command_receipts.command_id"), nullable=False
    ),
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
    CheckConstraint("event_schema_name = 'employer.created'", name="ck_audit_events_schema_name"),
    CheckConstraint("event_schema_version = 1", name="ck_audit_events_schema_version"),
    CheckConstraint("event_type = 'employer.created'", name="ck_audit_events_event_type"),
    CheckConstraint("entity_type = 'employer'", name="ck_audit_events_entity_type"),
    CheckConstraint("actor_type = 'staff'", name="ck_audit_events_actor_type"),
    CheckConstraint("source_type = 'staff_api'", name="ck_audit_events_source_type"),
    CheckConstraint(
        "payload_classification = 'sensitive_operational'",
        name="ck_audit_events_payload_classification",
    ),
)
