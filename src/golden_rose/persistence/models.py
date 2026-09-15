from typing import Any

from sqlalchemy import (
    Boolean,
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
    Column("intake_id", UUID(as_uuid=True), nullable=True),
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
        "entity_type IN ('employer', 'employer_contact', 'intake')",
        name="ck_entity_authorities_entity_type",
    ),
    ForeignKeyConstraint(
        ["intake_id"],
        ["intakes.intake_id"],
        name="fk_entity_authorities_intake",
        deferrable=True,
        initially="DEFERRED",
    ),
    UniqueConstraint("intake_id", name="uq_entity_authorities_intake_id"),
    CheckConstraint(
        "(entity_type='employer' AND employer_id IS NOT NULL AND employer_id=entity_id "
        "AND employer_contact_id IS NULL AND intake_id IS NULL) OR "
        "(entity_type='employer_contact' AND employer_contact_id IS NOT NULL "
        "AND employer_contact_id=entity_id AND employer_id IS NULL AND intake_id IS NULL) OR "
        "(entity_type='intake' AND intake_id IS NOT NULL AND intake_id=entity_id "
        "AND employer_id IS NULL AND employer_contact_id IS NULL)",
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
        ", 'create_intake', 'revise_intake', 'revise_intake_address'"
        ")",
        name="ck_command_receipts_command_type",
    ),
    CheckConstraint(
        "octet_length(request_fingerprint) = 32", name="ck_command_receipts_request_fingerprint_len"
    ),
    CheckConstraint(
        "result_entity_type IN ('employer', 'employer_contact', 'intake')",
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
        "AND result_record_version >= 2) OR "
        "(command_type='create_intake' AND result_entity_type='intake' "
        "AND result_event_type='intake.created' AND result_record_version=1) OR "
        "(command_type IN ('revise_intake','revise_intake_address') AND result_entit"
        "y_type='intake' "
        "AND result_event_type='intake.revised' AND result_record_version>=2))",
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
        "'employer.created', 'employer_contact.created', 'employer.draft_revised', '"
        "intake.created', 'intake.revised'"
        ")",
        name="ck_audit_events_schema_name",
    ),
    CheckConstraint("event_schema_name = event_type", name="ck_audit_events_schema_matches_type"),
    CheckConstraint("event_schema_version = 1", name="ck_audit_events_schema_version"),
    CheckConstraint(
        "event_type IN ('employer.created', 'employer_contact.created', 'employer.dr"
        "aft_revised', 'intake.created', 'intake.revised')",
        name="ck_audit_events_event_type",
    ),
    CheckConstraint(
        "entity_type IN ('employer', 'employer_contact', 'intake')",
        name="ck_audit_events_entity_type",
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
            "command_results.command_id",
            "command_results.entity_type",
            "command_results.entity_id",
            "command_results.result_version",
            "command_results.event_type",
            "command_results.actor_id",
        ],
        name="fk_audit_events_command_result",
        deferrable=True,
        initially="DEFERRED",
    ),
)


intakes = Table(
    "intakes",
    metadata,
    Column("intake_id", UUID(as_uuid=True), primary_key=True),
    Column("kind", String(32), nullable=False),
    Column("schema_version", Integer, nullable=False),
    Column("content", JSONB, nullable=False),
    Column("lifecycle_status", String(32), nullable=False),
    Column("version", Integer, nullable=False),
    Column("content_version", Integer, nullable=False),
    Column("created_at", TIMESTAMP(timezone=True), nullable=False),
    Column("created_by", UUID(as_uuid=True), nullable=False),
    Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
    Column("updated_by", UUID(as_uuid=True), nullable=False),
    CheckConstraint("kind IN ('worker','employer')", name="ck_intakes_kind"),
    CheckConstraint("schema_version=1", name="ck_intakes_schema_version"),
    CheckConstraint("lifecycle_status='draft'", name="ck_intakes_lifecycle_draft"),
    CheckConstraint("version>=1", name="ck_intakes_version_positive"),
    CheckConstraint(
        "content_version>=1 AND content_version<=version", name="ck_intakes_content_version"
    ),
    CheckConstraint("jsonb_typeof(content)='object'", name="ck_intakes_content_object"),
    CheckConstraint("octet_length(content::text)<=32768", name="ck_intakes_content_size"),
    CheckConstraint(
        "(kind='worker' AND content - ARRAY['full_name','phone','interests','availab"
        "ility']::text[]='{}'::jsonb) OR "
        "(kind='employer' AND content - ARRAY['employer_type','display_name','representative_name',"
        "'phone','role_title','duties_summary','worker_count','schedule','offer']::t"
        "ext[]='{}'::jsonb)",
        name="ck_intakes_content_kind",
    ),
    UniqueConstraint("intake_id", "kind", name="uq_intakes_id_kind"),
)

intake_addresses = Table(
    "intake_addresses",
    metadata,
    Column("intake_id", UUID(as_uuid=True), primary_key=True),
    Column("section", String(32), primary_key=True),
    Column("line1", String(200)),
    Column("line2", String(200)),
    Column("locality", String(100)),
    Column("region", String(100)),
    Column("postal_code", String(32)),
    Column("country", String(2)),
    ForeignKeyConstraint(["intake_id"], ["intakes.intake_id"], name="fk_intake_addresses_intake"),
    CheckConstraint(
        "section IN ('worker_residence','party_address','worksite_address')",
        name="ck_intake_addresses_section",
    ),
    CheckConstraint(
        "(line1 IS NULL OR btrim(line1)<>'') AND (line2 IS NULL OR btrim(line2)<>'') "
        "AND (locality IS NULL OR btrim(locality)<>'') AND (region IS NULL OR btrim(region)<>'') "
        "AND (postal_code IS NULL OR btrim(postal_code)<>'')",
        name="ck_intake_addresses_nonblank",
    ),
    CheckConstraint(
        "country IS NULL OR country ~ '^[A-Z]{2}$'", name="ck_intake_addresses_country"
    ),
)

intake_links = Table(
    "intake_links",
    metadata,
    Column("intake_id", UUID(as_uuid=True), primary_key=True),
    ForeignKeyConstraint(["intake_id"], ["intakes.intake_id"], name="fk_intake_links_intake"),
    CheckConstraint("false", name="ck_intake_links_not_available"),
)

command_results = Table(
    "command_results",
    metadata,
    Column("command_id", UUID(as_uuid=True), primary_key=True),
    Column("entity_type", String(32), primary_key=True),
    Column("entity_id", UUID(as_uuid=True), primary_key=True),
    Column("result_version", Integer, nullable=False),
    Column("event_type", String(64), nullable=False),
    Column("actor_id", UUID(as_uuid=True), nullable=False),
    Column("command_type", String(64), nullable=False),
    UniqueConstraint(
        "command_id",
        "entity_type",
        "entity_id",
        "result_version",
        "event_type",
        "actor_id",
        name="uq_command_results_exact_authority",
    ),
    CheckConstraint("result_version>=1", name="ck_command_results_version_positive"),
    ForeignKeyConstraint(
        ["entity_type", "entity_id"],
        ["entity_authorities.entity_type", "entity_authorities.entity_id"],
        name="fk_command_results_entity_authority",
        deferrable=True,
        initially="DEFERRED",
    ),
    ForeignKeyConstraint(
        ["command_id", "actor_id", "command_type"],
        [
            "command_receipts.command_id",
            "command_receipts.actor_id",
            "command_receipts.command_type",
        ],
        name="fk_command_results_receipt_actor_type",
        deferrable=True,
        initially="DEFERRED",
    ),
    ForeignKeyConstraint(
        ["command_id", "entity_id", "result_version", "event_type", "actor_id"],
        [
            "audit_events.command_id",
            "audit_events.entity_id",
            "audit_events.new_record_version",
            "audit_events.event_type",
            "audit_events.actor_id",
        ],
        name="fk_command_results_exact_audit",
        deferrable=True,
        initially="DEFERRED",
    ),
    ForeignKeyConstraint(
        ["command_id", "entity_type", "entity_id"],
        ["audit_events.command_id", "audit_events.entity_type", "audit_events.entity_id"],
        name="fk_command_results_typed_audit",
        deferrable=True,
        initially="DEFERRED",
    ),
)
command_receipts.append_constraint(
    UniqueConstraint(
        "command_id", "actor_id", "command_type", name="uq_command_receipts_actor_command"
    )
)
command_receipts.append_constraint(
    ForeignKeyConstraint(
        [
            "command_id",
            "result_entity_type",
            "result_entity_id",
            "result_record_version",
            "result_event_type",
            "actor_id",
        ],
        [
            "command_results.command_id",
            "command_results.entity_type",
            "command_results.entity_id",
            "command_results.result_version",
            "command_results.event_type",
            "command_results.actor_id",
        ],
        name="fk_command_receipts_primary_result",
        deferrable=True,
        initially="DEFERRED",
    )
)
_receipt_shape = next(
    c
    for c in command_receipts.constraints
    if isinstance(c, CheckConstraint) and c.name == "ck_command_receipts_result_authority_shape"
)
command_results.append_constraint(
    CheckConstraint(
        str(_receipt_shape.sqltext)
        .replace("result_entity_type", "entity_type")
        .replace("result_event_type", "event_type")
        .replace("result_record_version", "result_version"),
        name="ck_command_results_authority_shape",
    )
)


# PR B workflow history is append-only; sensitive values have separate tables.
intake_reviews = Table(
    "intake_reviews",
    metadata,
    Column("review_id", UUID(as_uuid=True), primary_key=True),
    Column("intake_id", UUID(as_uuid=True), nullable=False),
    Column("command_id", UUID(as_uuid=True), nullable=False),
    Column("event_id", UUID(as_uuid=True), nullable=False),
    Column("reviewed_record_version", Integer, nullable=False),
    Column("reviewed_content_version", Integer, nullable=False),
    Column("result_version", Integer, nullable=False),
    Column("outcome", String(32), nullable=False),
    Column("actor_id", UUID(as_uuid=True), nullable=False),
    Column("actor_display_name", String(200), nullable=False),
    Column("occurred_at", TIMESTAMP(timezone=True), nullable=False),
)
intake_review_payloads = Table(
    "intake_review_payloads",
    metadata,
    Column("review_id", UUID(as_uuid=True), primary_key=True),
    Column("reviewed_content", JSONB, nullable=False),
    Column("note", String(512)),
    Column("dependency_refs", JSONB, nullable=False, server_default="{}"),
)
intake_follow_up_events = Table(
    "intake_follow_up_events",
    metadata,
    Column("event_id", UUID(as_uuid=True), primary_key=True),
    Column("intake_id", UUID(as_uuid=True), nullable=False),
    Column("command_id", UUID(as_uuid=True), nullable=False),
    Column("version", Integer, nullable=False),
    Column("content_version", Integer, nullable=False),
    Column("action", String(32), nullable=False),
    Column("actor_id", UUID(as_uuid=True), nullable=False),
    Column("actor_display_name", String(200), nullable=False),
    Column("occurred_at", TIMESTAMP(timezone=True), nullable=False),
    Column("owner_staff_id", UUID(as_uuid=True), nullable=False),
    Column("next_follow_up_at", TIMESTAMP(timezone=True), nullable=False),
    Column("time_zone", String(100), nullable=False),
    Column("reason_code", String(32)),
    Column("method", String(32)),
    Column("outcome", String(64)),
    Column("review_id", UUID(as_uuid=True)),
)
intake_history_payloads = Table(
    "intake_history_payloads",
    metadata,
    Column("event_id", UUID(as_uuid=True), primary_key=True),
    Column("reason_text", String(512), nullable=False),
    Column("note", String(512)),
)
work_interests = Table(
    "work_interests",
    metadata,
    Column("interest_id", UUID(as_uuid=True), primary_key=True),
    Column("code", String(64), nullable=False),
    Column("version", Integer, nullable=False),
    Column("label_en", String(100), nullable=False),
    Column("label_es", String(100), nullable=False),
    Column("active", Boolean, nullable=False),
    Column("created_at", TIMESTAMP(timezone=True), nullable=False),
    Column("created_by", UUID(as_uuid=True), nullable=False),
    Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
    Column("updated_by", UUID(as_uuid=True), nullable=False),
)
work_interest_versions = Table(
    "work_interest_versions",
    metadata,
    Column("interest_id", UUID(as_uuid=True), primary_key=True),
    Column("version", Integer, primary_key=True),
    Column("label_en", String(100), nullable=False),
    Column("label_es", String(100), nullable=False),
    Column("active", Boolean, nullable=False),
    Column("actor_id", UUID(as_uuid=True), nullable=False),
    Column("occurred_at", TIMESTAMP(timezone=True), nullable=False),
    Column("command_id", UUID(as_uuid=True), nullable=False),
)
entity_authorities.append_column(Column("work_interest_id", UUID(as_uuid=True)))


# Keep metadata's exhaustive authority arms aligned with migration 0007.
def _replace_check(table: Table, name: str, sql: str) -> None:
    prior = next(c for c in table.constraints if c.name == name)
    table.constraints.remove(prior)
    table.append_constraint(CheckConstraint(sql, name=name))


_types = ("employer", "employer_contact", "intake", "work_interest")
for _table, _name, _column in (
    (entity_authorities, "ck_entity_authorities_entity_type", "entity_type"),
    (command_receipts, "ck_command_receipts_entity_type", "result_entity_type"),
    (audit_events, "ck_audit_events_entity_type", "entity_type"),
):
    _replace_check(_table, _name, f"{_column} IN (" + ",".join(repr(v) for v in _types) + ")")
_replace_check(
    entity_authorities,
    "ck_entity_authorities_exactly_one_concrete_id",
    " OR ".join(
        f"(entity_type='{kind}' AND {kind}_id IS NOT NULL AND {kind}_id=entity_id AND "
        + " AND ".join(f"{other}_id IS NULL" for other in _types if other != kind)
        + ")"
        for kind in _types
    ),
)
entity_authorities.append_constraint(
    ForeignKeyConstraint(
        ["work_interest_id"],
        ["work_interests.interest_id"],
        name="fk_entity_authorities_work_interest",
        deferrable=True,
        initially="DEFERRED",
    )
)
entity_authorities.append_constraint(UniqueConstraint("work_interest_id"))
_new_commands = {
    "review_intake": ("intake", "intake.reviewed", ">=2"),
    "follow_up_intake": ("intake", "intake.follow_up_recorded", ">=2"),
    "create_work_interest": ("work_interest", "work_interest.created", "=1"),
    "revise_work_interest": ("work_interest", "work_interest.revised", ">=2"),
}
for _table, _name, _column, _values in (
    (command_receipts, "ck_command_receipts_command_type", "command_type", list(_new_commands)),
    (
        audit_events,
        "ck_audit_events_event_type",
        "event_type",
        [v[1] for v in _new_commands.values()],
    ),
    (
        audit_events,
        "ck_audit_events_schema_name",
        "event_schema_name",
        [v[1] for v in _new_commands.values()],
    ),
):
    _prior = next(
        c for c in _table.constraints if isinstance(c, CheckConstraint) and c.name == _name
    )
    _replace_check(
        _table,
        _name,
        "("
        + str(_prior.sqltext)
        + ") OR "
        + _column
        + " IN ("
        + ",".join(repr(v) for v in _values)
        + ")",
    )
for _table, _name, _prefix in (
    (command_receipts, "ck_command_receipts_result_authority_shape", "result_"),
    (command_results, "ck_command_results_authority_shape", ""),
):
    _prior = next(
        c for c in _table.constraints if isinstance(c, CheckConstraint) and c.name == _name
    )
    _version = "result_record_version" if _prefix else "result_version"
    _sql = (
        "("
        + str(_prior.sqltext)
        + ") OR "
        + " OR ".join(
            f"(command_type='{cmd}' AND {_prefix}entity_type='{entity}' "
            f"AND {_prefix}event_type='{event}' AND {_version}{version})"
            for cmd, (entity, event, version) in _new_commands.items()
        )
    )
    _replace_check(_table, _name, _sql)

# Concrete workflow relationships and scalar invariants mirror migration 0007.
work_interests.append_constraint(
    CheckConstraint("code::text ~ '^[a-z0-9_]{1,64}$'::text", name="ck_work_interests_code")
)
work_interests.append_constraint(
    CheckConstraint("btrim(label_en::text) <> ''::text", name="work_interests_label_en_check")
)
work_interests.append_constraint(
    CheckConstraint("btrim(label_es::text) <> ''::text", name="work_interests_label_es_check")
)
work_interests.append_constraint(
    CheckConstraint("version >= 1", name="work_interests_version_check")
)
work_interests.append_constraint(UniqueConstraint("code", name="work_interests_code_key"))
work_interest_versions.append_constraint(
    CheckConstraint(
        "btrim(label_en::text) <> ''::text", name="work_interest_versions_label_en_check"
    )
)
work_interest_versions.append_constraint(
    CheckConstraint(
        "btrim(label_es::text) <> ''::text", name="work_interest_versions_label_es_check"
    )
)
work_interest_versions.append_constraint(
    CheckConstraint("version >= 1", name="work_interest_versions_version_check")
)
work_interest_versions.append_constraint(
    UniqueConstraint("command_id", name="work_interest_versions_command_id_key")
)
work_interest_versions.append_constraint(
    ForeignKeyConstraint(
        ["command_id"],
        ["command_receipts.command_id"],
        name="work_interest_versions_command_id_fkey",
        deferrable=True,
        initially="DEFERRED",
    )
)
work_interest_versions.append_constraint(
    ForeignKeyConstraint(
        ["interest_id"],
        ["work_interests.interest_id"],
        name="work_interest_versions_interest_id_fkey",
    )
)
intake_reviews.append_constraint(
    CheckConstraint(
        "btrim(actor_display_name::text) <> ''::text",
        name="intake_reviews_actor_display_name_check",
    )
)
intake_reviews.append_constraint(
    CheckConstraint(
        "reviewed_content_version >= 1 AND reviewed_content_version <= reviewed_record_version",
        name="intake_reviews_check",
    )
)
intake_reviews.append_constraint(
    CheckConstraint("result_version = (reviewed_record_version + 1)", name="intake_reviews_check1")
)
intake_reviews.append_constraint(
    CheckConstraint(
        (
            "outcome::text = ANY (ARRAY['intake_reviewed'::character varying, "
            "'needs_follow_up'::character varying]::text[])"
        ),
        name="intake_reviews_outcome_check",
    )
)
intake_reviews.append_constraint(
    CheckConstraint(
        "reviewed_record_version >= 1", name="intake_reviews_reviewed_record_version_check"
    )
)
intake_reviews.append_constraint(
    UniqueConstraint("command_id", name="intake_reviews_command_id_key")
)
intake_reviews.append_constraint(UniqueConstraint("event_id", name="intake_reviews_event_id_key"))
intake_reviews.append_constraint(
    UniqueConstraint(
        "intake_id", "result_version", name="intake_reviews_intake_id_result_version_key"
    )
)
intake_reviews.append_constraint(
    UniqueConstraint("intake_id", "review_id", name="intake_reviews_intake_id_review_id_key")
)
intake_reviews.append_constraint(
    ForeignKeyConstraint(
        ["review_id"],
        ["intake_review_payloads.review_id"],
        name="fk_intake_reviews_required_payload",
        deferrable=True,
        initially="DEFERRED",
    )
)
intake_reviews.append_constraint(
    ForeignKeyConstraint(
        ["command_id"],
        ["command_receipts.command_id"],
        name="intake_reviews_command_id_fkey",
        deferrable=True,
        initially="DEFERRED",
    )
)
intake_reviews.append_constraint(
    ForeignKeyConstraint(
        ["event_id"],
        ["audit_events.audit_event_id"],
        name="intake_reviews_event_id_fkey",
        deferrable=True,
        initially="DEFERRED",
    )
)
intake_reviews.append_constraint(
    ForeignKeyConstraint(["intake_id"], ["intakes.intake_id"], name="intake_reviews_intake_id_fkey")
)
intake_review_payloads.append_constraint(
    CheckConstraint(
        "dependency_refs = '{}'::jsonb", name="intake_review_payloads_dependency_refs_check"
    )
)
intake_review_payloads.append_constraint(
    CheckConstraint(
        "note IS NULL OR btrim(note::text) <> ''::text", name="intake_review_payloads_note_check"
    )
)
intake_review_payloads.append_constraint(
    CheckConstraint(
        "jsonb_typeof(reviewed_content) = 'object'::text",
        name="intake_review_payloads_reviewed_content_check",
    )
)
intake_review_payloads.append_constraint(
    ForeignKeyConstraint(
        ["review_id"],
        ["intake_reviews.review_id"],
        name="intake_review_payloads_review_id_fkey",
        deferrable=True,
        initially="DEFERRED",
    )
)
intake_follow_up_events.append_constraint(
    CheckConstraint(
        (
            "action::text = 'needs_follow_up'::text AND review_id IS NOT NULL "
            "AND reason_code IS NOT NULL AND (reason_code::text = ANY (ARRAY['"
            "missing_information'::character varying, 'clarification'::charact"
            "er varying, 'other'::character varying]::text[])) AND method IS N"
            "ULL AND outcome IS NULL OR (action::text = ANY (ARRAY['reschedule"
            "'::character varying, 'reassign'::character varying]::text[])) AN"
            "D review_id IS NULL AND reason_code IS NULL AND method IS NULL AN"
            "D outcome IS NULL OR action::text = 'attempt'::text AND review_id"
            " IS NULL AND reason_code IS NULL AND method IS NOT NULL AND (meth"
            "od::text = ANY (ARRAY['phone'::character varying, 'email'::charac"
            "ter varying, 'in_person'::character varying, 'other'::character v"
            "arying]::text[])) AND outcome IS NOT NULL AND (outcome::text = AN"
            "Y (ARRAY['no_answer'::character varying, 'voicemail_left'::charac"
            "ter varying, 'callback_requested'::character varying, 'contact_re"
            "ached_information_pending'::character varying, 'invalid_contact_i"
            "nformation'::character varying, 'information_received'::character"
            " varying, 'other'::character varying]::text[]))"
        ),
        name="ck_intake_follow_up_shape",
    )
)
intake_follow_up_events.append_constraint(
    CheckConstraint(
        (
            "action::text = ANY (ARRAY['needs_follow_up'::character varying, '"
            "reschedule'::character varying, 'reassign'::character varying, 'a"
            "ttempt'::character varying]::text[])"
        ),
        name="intake_follow_up_events_action_check",
    )
)
intake_follow_up_events.append_constraint(
    CheckConstraint(
        "btrim(actor_display_name::text) <> ''::text",
        name="intake_follow_up_events_actor_display_name_check",
    )
)
intake_follow_up_events.append_constraint(
    CheckConstraint(
        "content_version >= 1 AND content_version < version", name="intake_follow_up_events_check"
    )
)
intake_follow_up_events.append_constraint(
    CheckConstraint(
        "btrim(time_zone::text) <> ''::text", name="intake_follow_up_events_time_zone_check"
    )
)
intake_follow_up_events.append_constraint(
    CheckConstraint("version >= 2", name="intake_follow_up_events_version_check")
)
intake_follow_up_events.append_constraint(
    UniqueConstraint("command_id", name="intake_follow_up_events_command_id_key")
)
intake_follow_up_events.append_constraint(
    UniqueConstraint("intake_id", "version", name="intake_follow_up_events_intake_id_version_key")
)
intake_follow_up_events.append_constraint(
    ForeignKeyConstraint(
        ["event_id"],
        ["intake_history_payloads.event_id"],
        name="fk_intake_follow_up_required_payload",
        deferrable=True,
        initially="DEFERRED",
    )
)
intake_follow_up_events.append_constraint(
    ForeignKeyConstraint(
        ["command_id"],
        ["command_receipts.command_id"],
        name="intake_follow_up_events_command_id_fkey",
        deferrable=True,
        initially="DEFERRED",
    )
)
intake_follow_up_events.append_constraint(
    ForeignKeyConstraint(
        ["event_id"],
        ["audit_events.audit_event_id"],
        name="intake_follow_up_events_event_id_fkey",
        deferrable=True,
        initially="DEFERRED",
    )
)
intake_follow_up_events.append_constraint(
    ForeignKeyConstraint(
        ["intake_id"], ["intakes.intake_id"], name="intake_follow_up_events_intake_id_fkey"
    )
)
intake_follow_up_events.append_constraint(
    ForeignKeyConstraint(
        ["intake_id", "review_id"],
        ["intake_reviews.intake_id", "intake_reviews.review_id"],
        name="intake_follow_up_events_intake_id_review_id_fkey",
        deferrable=True,
        initially="DEFERRED",
    )
)
intake_history_payloads.append_constraint(
    CheckConstraint(
        "note IS NULL OR btrim(note::text) <> ''::text", name="intake_history_payloads_note_check"
    )
)
intake_history_payloads.append_constraint(
    CheckConstraint(
        "btrim(reason_text::text) <> ''::text", name="intake_history_payloads_reason_text_check"
    )
)
intake_history_payloads.append_constraint(
    ForeignKeyConstraint(
        ["event_id"],
        ["intake_follow_up_events.event_id"],
        name="intake_history_payloads_event_id_fkey",
        deferrable=True,
        initially="DEFERRED",
    )
)


# PR C's first slice supports creation of a complete new worker group only.
def _canonical_attribution() -> list[Column[Any]]:
    return [
        Column("version", Integer, nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False),
        Column("created_by", UUID(as_uuid=True), nullable=False),
        Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        Column("updated_by", UUID(as_uuid=True), nullable=False),
    ]


workers = Table(
    "workers",
    metadata,
    Column("worker_id", UUID(as_uuid=True), primary_key=True),
    Column("full_name", String(200), nullable=False),
    *_canonical_attribution(),
)
worker_contacts = Table(
    "worker_contacts",
    metadata,
    Column("worker_contact_id", UUID(as_uuid=True), primary_key=True),
    Column("worker_id", UUID(as_uuid=True), nullable=False),
    Column("phone", String(32), nullable=False),
    *_canonical_attribution(),
)
worker_residences = Table(
    "worker_residences",
    metadata,
    Column("worker_residence_id", UUID(as_uuid=True), primary_key=True),
    Column("worker_id", UUID(as_uuid=True), nullable=False),
    Column("line1", String(200), nullable=False),
    Column("line2", String(200)),
    Column("locality", String(100), nullable=False),
    Column("region", String(100)),
    Column("postal_code", String(32)),
    Column("country", String(2), nullable=False),
    *_canonical_attribution(),
)
worker_preferences = Table(
    "worker_preferences",
    metadata,
    Column("worker_preferences_id", UUID(as_uuid=True), primary_key=True),
    Column("worker_id", UUID(as_uuid=True), nullable=False),
    Column("interests", JSONB, nullable=False),
    Column("availability", JSONB, nullable=False),
    Column("self_reported", Boolean, nullable=False),
    *_canonical_attribution(),
)
worker_interest_selections = Table(
    "worker_interest_selections",
    metadata,
    Column("worker_preferences_id", UUID(as_uuid=True), primary_key=True),
    Column("interest_id", UUID(as_uuid=True), primary_key=True),
    Column("catalog_version", Integer, nullable=False),
)
intake_finalizations = Table(
    "intake_finalizations",
    metadata,
    Column("intake_id", UUID(as_uuid=True), primary_key=True),
    Column("command_id", UUID(as_uuid=True), nullable=False),
    Column("review_id", UUID(as_uuid=True), nullable=False),
    Column("content_version", Integer, nullable=False),
    Column("result_version", Integer, nullable=False),
    Column("kind", String(32), nullable=False),
    Column("actor_id", UUID(as_uuid=True), nullable=False),
    Column("occurred_at", TIMESTAMP(timezone=True), nullable=False),
)
for _kind in ("worker", "worker_contact", "worker_residence", "worker_preferences"):
    entity_authorities.append_column(Column(f"{_kind}_id", UUID(as_uuid=True)))
    intake_finalizations.append_column(Column(f"{_kind}_id", UUID(as_uuid=True)))
    intake_finalizations.append_column(Column(f"{_kind}_version", Integer))
    intake_finalizations.append_column(Column(f"{_kind}_disposition", String(16)))


def _employer_output_address(*, nullable: bool) -> list[Column[Any]]:
    return [
        Column("line1", String(200), nullable=nullable),
        Column("line2", String(200)),
        Column("locality", String(100), nullable=nullable),
        Column("region", String(100)),
        Column("postal_code", String(32)),
        Column("country", String(2), nullable=nullable),
    ]


# Column mappings for the additive employer-finalization migration extension.
employer_contact_details = Table(
    "employer_contact_details",
    metadata,
    Column("employer_contact_details_id", UUID(as_uuid=True), primary_key=True),
    Column("employer_id", UUID(as_uuid=True), nullable=False),
    Column("employer_contact_id", UUID(as_uuid=True), nullable=False, unique=True),
    Column("representative_name", String(200), nullable=False),
    Column("phone", String(40), nullable=False),
    *_employer_output_address(nullable=True),
    *_canonical_attribution(),
    ForeignKeyConstraint(
        ["employer_id", "employer_contact_id"],
        ["employer_contacts.employer_id", "employer_contacts.employer_contact_id"],
    ),
    UniqueConstraint("employer_id", "employer_contact_details_id"),
)
employer_addresses = Table(
    "employer_addresses",
    metadata,
    Column("employer_address_id", UUID(as_uuid=True), primary_key=True),
    Column("employer_id", UUID(as_uuid=True), nullable=False),
    Column("purpose", String(32), nullable=False),
    *_employer_output_address(nullable=False),
    *_canonical_attribution(),
    ForeignKeyConstraint(["employer_id"], ["employers.employer_id"]),
    UniqueConstraint("employer_id", "employer_address_id"),
)
worksites = Table(
    "worksites",
    metadata,
    Column("worksite_id", UUID(as_uuid=True), primary_key=True),
    Column("employer_id", UUID(as_uuid=True), nullable=False),
    Column("location_verification_status", String(32), nullable=False),
    Column("service_area_status", String(32), nullable=False),
    Column("map_area_status", String(32), nullable=False),
    *_employer_output_address(nullable=False),
    *_canonical_attribution(),
    ForeignKeyConstraint(["employer_id"], ["employers.employer_id"]),
    UniqueConstraint("employer_id", "worksite_id"),
)
staffing_requests = Table(
    "staffing_requests",
    metadata,
    Column("staffing_request_id", UUID(as_uuid=True), primary_key=True),
    Column("employer_id", UUID(as_uuid=True), nullable=False),
    Column("employer_contact_id", UUID(as_uuid=True), nullable=False),
    Column("worksite_id", UUID(as_uuid=True), nullable=False),
    Column("employer_address_id", UUID(as_uuid=True)),
    Column("request_type", String(32), nullable=False),
    Column("request_status", String(32), nullable=False),
    Column("source_channel", String(32), nullable=False),
    Column("received_at", TIMESTAMP(timezone=True), nullable=False),
    Column("role_title", String(200), nullable=False),
    Column("duties_summary", String(1000), nullable=False),
    Column("worker_count", Integer, nullable=False),
    Column("schedule", JSONB, nullable=False),
    Column("offer", JSONB, nullable=False),
    *_canonical_attribution(),
    ForeignKeyConstraint(["employer_id"], ["employers.employer_id"]),
    ForeignKeyConstraint(
        ["employer_id", "employer_contact_id"],
        ["employer_contacts.employer_id", "employer_contacts.employer_contact_id"],
    ),
    ForeignKeyConstraint(
        ["employer_id", "worksite_id"], ["worksites.employer_id", "worksites.worksite_id"]
    ),
    ForeignKeyConstraint(
        ["employer_id", "employer_address_id"],
        ["employer_addresses.employer_id", "employer_addresses.employer_address_id"],
    ),
    UniqueConstraint("employer_id", "staffing_request_id"),
)
for _kind in ("employer_contact_details", "employer_address", "worksite", "staffing_request"):
    entity_authorities.append_column(Column(f"{_kind}_id", UUID(as_uuid=True)))

for _kind in (
    "employer",
    "employer_contact",
    "employer_contact_details",
    "employer_address",
    "worksite",
    "staffing_request",
):
    intake_finalizations.append_column(Column(f"{_kind}_id", UUID(as_uuid=True)))
    intake_finalizations.append_column(Column(f"{_kind}_version", Integer))
    intake_finalizations.append_column(Column(f"{_kind}_disposition", String(16)))
