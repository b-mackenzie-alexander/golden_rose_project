from __future__ import annotations

import os
from collections import defaultdict
from collections.abc import Iterable
from contextlib import suppress

from sqlalchemy import text
from sqlalchemy.engine import Connection, create_engine
from sqlalchemy.exc import SQLAlchemyError

from golden_rose.database import get_database_url

SCHEMA_OWNER_ROLE = "golden_rose_schema_owner"
MIGRATOR_ROLE = "golden_rose_migrator"
RUNTIME_ROLE = "golden_rose_runtime"
PUBLIC_ROLE = "PUBLIC"

EXPECTED_RUNTIME_TABLE_PRIVILEGES: dict[str, set[str]] = {
    "work_interests": {"INSERT", "SELECT"},
    "work_interest_versions": {"INSERT", "SELECT"},
    "intake_reviews": {"INSERT", "SELECT"},
    "intake_review_payloads": {"INSERT", "SELECT"},
    "intake_follow_up_events": {"INSERT", "SELECT"},
    "intake_history_payloads": {"INSERT", "SELECT"},
    "alembic_version": {"SELECT"},
    "employers": {"INSERT", "SELECT", "UPDATE"},
    "employer_contacts": {"INSERT", "SELECT"},
    "entity_authorities": {"INSERT", "SELECT"},
    "command_receipts": {"INSERT", "SELECT"},
    "audit_events": {"INSERT", "SELECT"},
    "intakes": {"INSERT", "SELECT"},
    "intake_addresses": {"INSERT", "SELECT"},
    "intake_links": {"INSERT", "SELECT"},
    "command_results": {"INSERT", "SELECT"},
}
EXPECTED_RUNTIME_SCHEMA_PRIVILEGES: set[str] = {"USAGE"}
EXPECTED_RUNTIME_FUNCTION_PRIVILEGES: dict[str, set[str]] = {
    "guard_intake_workflow_authority": set(),
    "guard_work_interest_identity": set(),
    "guard_work_interest_authority": set(),
    "deny_mutation_on_append_only_tables": set(),
    "populate_employer_revision_compatibility_fields": set(),
    "populate_command_receipt_revision_compatibility_fields": set(),
    "populate_legacy_command_result": set(),
    "guard_intake_identity": set(),
    "guard_intake_write_authority": set(),
    "guard_intake_address_authority": set(),
}
EXPECTED_DEFAULT_PRIVILEGES: dict[str, set[str]] = {
    "tables": {"INSERT", "SELECT"},
    "sequences": {"SELECT", "USAGE"},
    "functions": set(),
}
EXPECTED_PUBLIC_DEFAULT_PRIVILEGES: dict[str, set[str]] = {
    "tables": set(),
    "sequences": set(),
    "functions": set(),
}
EXPECTED_SCHEMA_OWNER_OBJECTS: set[str] = {
    "work_interests",
    "work_interest_versions",
    "intake_reviews",
    "intake_review_payloads",
    "intake_follow_up_events",
    "intake_history_payloads",
    "alembic_version",
    "employers",
    "employer_contacts",
    "entity_authorities",
    "command_receipts",
    "audit_events",
    "intakes",
    "intake_addresses",
    "intake_links",
    "command_results",
}
EXPECTED_SCHEMA_OWNER_FUNCTIONS: set[str] = {
    "guard_intake_workflow_authority",
    "guard_work_interest_identity",
    "guard_work_interest_authority",
    "deny_mutation_on_append_only_tables",
    "populate_employer_revision_compatibility_fields",
    "populate_command_receipt_revision_compatibility_fields",
    "populate_legacy_command_result",
    "guard_intake_identity",
    "guard_intake_write_authority",
    "guard_intake_address_authority",
}
DEFAULT_PRIVILEGE_OBJECT_TYPE_MAP: dict[str, str] = {
    "r": "tables",
    "S": "sequences",
    "f": "functions",
}

DATABASE_IDENTITY_QUERY = text(
    """
    SELECT
        current_database() AS database_name,
        COALESCE(inet_server_addr()::text, 'local') AS server_addr,
        COALESCE(inet_server_port(), 0) AS server_port
    """
)

ROLE_ATTRIBUTES_QUERY = text(
    """
    SELECT rolname, rolcanlogin, rolsuper, rolcreaterole, rolcreatedb,
           rolreplication, rolbypassrls, rolinherit
    FROM pg_roles
    WHERE rolname = ANY(:role_names)
    """
)

ROLE_MEMBERSHIP_QUERY = text(
    """
    SELECT member_role.rolname AS member, granted_role.rolname AS granted
    FROM pg_auth_members membership
    JOIN pg_roles member_role ON member_role.oid = membership.member
    JOIN pg_roles granted_role ON granted_role.oid = membership.roleid
    WHERE member_role.rolname = ANY(:role_names)
    """
)

# Include incoming edges as well as outgoing edges: a retained bootstrap or
# unsafe creator membership cannot be hidden by a names-only projection.
AUTHORITY_MEMBERSHIP_QUERY = text("""
    SELECT member_role.rolname AS member, granted_role.rolname AS granted,
           grantor.rolname AS grantor, grantor.rolsuper AS grantor_superuser,
           membership.admin_option, membership.inherit_option, membership.set_option
    FROM pg_auth_members membership
    JOIN pg_roles member_role ON member_role.oid = membership.member
    JOIN pg_roles granted_role ON granted_role.oid = membership.roleid
    JOIN pg_roles grantor ON grantor.oid = membership.grantor
    WHERE member_role.rolname = ANY(:role_names)
       OR granted_role.rolname = ANY(:role_names)
""")

SCHEMA_OWNER_QUERY = text(
    """
    SELECT pg_get_userbyid(nspowner) AS owner
    FROM pg_namespace
    WHERE nspname = 'public'
    """
)

TABLE_OWNER_QUERY = text(
    """
    SELECT class.relname AS object_name, pg_get_userbyid(class.relowner) AS owner
    FROM pg_class AS class
    JOIN pg_namespace AS namespace ON namespace.oid = class.relnamespace
    WHERE namespace.nspname = 'public'
      AND class.relkind = 'r'
      AND class.relname IN (
        'alembic_version',
        'employers',
        'employer_contacts',
        'entity_authorities',
        'command_receipts',
        'audit_events', 'intakes', 'intake_addresses', 'intake_links', 'command_results', 'work_interests','work_interest_versions','intake_reviews','intake_review_payloads','intake_follow_up_events','intake_history_payloads'
      )
    """
)

FUNCTION_OWNER_QUERY = text(
    """
    SELECT procedure.proname AS object_name, pg_get_userbyid(procedure.proowner) AS owner
    FROM pg_proc AS procedure
    JOIN pg_namespace AS namespace ON namespace.oid = procedure.pronamespace
    WHERE namespace.nspname = 'public'
      AND procedure.pronargs = 0
      AND procedure.proname = ANY(:function_names)
    """
)

PUBLIC_TABLE_PRIVILEGE_QUERY = text(
    """
    SELECT class.relname AS table_name, acl.privilege_type
    FROM pg_class AS class
    JOIN pg_namespace AS namespace ON namespace.oid = class.relnamespace
    CROSS JOIN LATERAL aclexplode(COALESCE(class.relacl, acldefault('r', class.relowner))) AS acl
    WHERE namespace.nspname = 'public'
      AND class.relkind = 'r'
      AND class.relname IN (
        'alembic_version', 'employers', 'employer_contacts',
        'entity_authorities', 'command_receipts', 'audit_events',
        'intakes', 'intake_addresses', 'intake_links', 'command_results', 'work_interests','work_interest_versions','intake_reviews','intake_review_payloads','intake_follow_up_events','intake_history_payloads'
      )
      AND acl.grantee = 0
    """
)

RUNTIME_TABLE_PRIVILEGE_QUERY = text(
    """
    WITH tables(table_name) AS (
        VALUES
            ('alembic_version'),
            ('employers'),
            ('employer_contacts'),
            ('entity_authorities'),
            ('command_receipts'),
            ('audit_events'), ('intakes'), ('intake_addresses'), ('intake_links'), ('command_results'), ('work_interests'),('work_interest_versions'),('intake_reviews'),('intake_review_payloads'),('intake_follow_up_events'),('intake_history_payloads')
    ),
    privileges(privilege_type) AS (
        VALUES
            ('SELECT'),
            ('INSERT'),
            ('UPDATE'),
            ('DELETE'),
            ('TRUNCATE'),
            ('REFERENCES'),
            ('TRIGGER')
    )
    SELECT
        tables.table_name,
        privileges.privilege_type,
        has_table_privilege(:runtime_role, format('public.%I', tables.table_name), privileges.privilege_type) AS allowed
    FROM tables
    CROSS JOIN privileges
    """
)

RUNTIME_SCHEMA_PRIVILEGE_QUERY = text(
    """
    WITH privileges(privilege_type) AS (
        VALUES ('USAGE'), ('CREATE')
    )
    SELECT
        privilege_type,
        has_schema_privilege(:runtime_role, 'public', privilege_type) AS allowed
    FROM privileges
    """
)

RUNTIME_FUNCTION_PRIVILEGE_QUERY = text(
    """
    SELECT function_name, has_function_privilege(:runtime_role, signature, 'EXECUTE') AS allowed
    FROM (
        VALUES
            ('deny_mutation_on_append_only_tables', 'public.deny_mutation_on_append_only_tables()'),
            ('populate_employer_revision_compatibility_fields', 'public.populate_employer_revision_compatibility_fields()'),
            ('populate_command_receipt_revision_compatibility_fields', 'public.populate_command_receipt_revision_compatibility_fields()'),
            ('populate_legacy_command_result', 'public.populate_legacy_command_result()'),
            ('guard_intake_identity', 'public.guard_intake_identity()'),
('guard_intake_workflow_authority', 'public.guard_intake_workflow_authority()'),('guard_work_interest_identity', 'public.guard_work_interest_identity()'),('guard_work_interest_authority', 'public.guard_work_interest_authority()'),
            ('guard_intake_write_authority', 'public.guard_intake_write_authority()'),
            ('guard_intake_address_authority', 'public.guard_intake_address_authority()')
    ) AS functions(function_name, signature)
    """
)

DEFAULT_PRIVILEGE_QUERY = text(
    """
    WITH object_types(objtype) AS (
        VALUES ('r'::"char"), ('S'::"char"), ('f'::"char")
    ),
    authority_acl AS (
        SELECT
            object_types.objtype,
            CASE
                WHEN default_acl.defaclobjtype IS NULL THEN acldefault(object_types.objtype, owner_role.oid)
                ELSE default_acl.defaclacl
            END AS acl
        FROM object_types
        CROSS JOIN pg_roles AS owner_role
        LEFT JOIN pg_default_acl AS default_acl
          ON default_acl.defaclrole = owner_role.oid
         AND default_acl.defaclobjtype = object_types.objtype
         AND (
            (object_types.objtype IN ('r'::"char", 'S'::"char")
             AND default_acl.defaclnamespace = 'public'::regnamespace)
            OR
            (object_types.objtype = 'f'::"char" AND default_acl.defaclnamespace = 0)
         )
        WHERE owner_role.rolname = :schema_owner
    )
    SELECT
        authority_acl.objtype,
        COALESCE(grantee_role.rolname, CASE WHEN acl.grantee = 0 THEN 'PUBLIC' END) AS grantee,
        acl.privilege_type
    FROM authority_acl
    LEFT JOIN LATERAL aclexplode(authority_acl.acl) AS acl ON TRUE
    LEFT JOIN pg_roles AS grantee_role ON grantee_role.oid = acl.grantee
    """
)


# UPDATE is column-scoped; granting whole-table UPDATE is deliberately rejected.
EXPECTED_RUNTIME_UPDATE_COLUMNS = {
    "work_interest_versions": set(),
    "intake_reviews": set(),
    "intake_review_payloads": set(),
    "intake_follow_up_events": set(),
    "intake_history_payloads": set(),
    "work_interests": {"version", "label_en", "label_es", "active", "updated_at", "updated_by"},
    "intakes": {"content", "version", "content_version", "updated_at", "updated_by"},
    "intake_addresses": {"line1", "line2", "locality", "region", "postal_code", "country"},
    "intake_links": set(),
    "command_results": set(),
}
# PostgreSQL 16 canonical definitions for the reviewed PR A/B constraint arms.
# Compare definitions as well as names: a same-name permissive CHECK must fail.
EXPECTED_INTAKE_CONSTRAINTS = {
    "audit_events.ck_audit_events_entity_type": "CHECK (entity_type::text = ANY "
    "(ARRAY['employer'::character varying, "
    "'employer_contact'::character varying, "
    "'intake'::character varying, "
    "'work_interest'::character varying]::text[]))",
    "audit_events.ck_audit_events_event_type": "CHECK (event_type::text = ANY "
    "(ARRAY['employer.created'::character varying, "
    "'employer_contact.created'::character varying, "
    "'employer.draft_revised'::character varying, "
    "'intake.created'::character varying, "
    "'intake.revised'::character varying, "
    "'intake.reviewed'::character varying, "
    "'intake.follow_up_recorded'::character varying, "
    "'work_interest.created'::character varying, "
    "'work_interest.revised'::character "
    "varying]::text[]))",
    "audit_events.ck_audit_events_schema_name": "CHECK (event_schema_name::text = ANY "
    "(ARRAY['employer.created'::character varying, "
    "'employer_contact.created'::character varying, "
    "'employer.draft_revised'::character varying, "
    "'intake.created'::character varying, "
    "'intake.revised'::character varying, "
    "'intake.reviewed'::character varying, "
    "'intake.follow_up_recorded'::character varying, "
    "'work_interest.created'::character varying, "
    "'work_interest.revised'::character "
    "varying]::text[]))",
    "audit_events.fk_audit_events_command_result": "FOREIGN KEY (command_id, entity_type, "
    "entity_id, new_record_version, event_type, "
    "actor_id) REFERENCES "
    "command_results(command_id, entity_type, "
    "entity_id, result_version, event_type, "
    "actor_id) DEFERRABLE INITIALLY DEFERRED",
    "audit_events.guard_intake_workflow_authority": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "audit_events.guard_work_interest_authority": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "command_receipts.ck_command_receipts_command_type": "CHECK (command_type::text = ANY "
    "(ARRAY['create_draft_employer'::character "
    "varying, "
    "'create_employer_contact'::character "
    "varying, "
    "'revise_draft_employer'::character "
    "varying, 'create_intake'::character "
    "varying, 'revise_intake'::character "
    "varying, "
    "'revise_intake_address'::character "
    "varying, 'review_intake'::character "
    "varying, 'follow_up_intake'::character "
    "varying, "
    "'create_work_interest'::character "
    "varying, "
    "'revise_work_interest'::character "
    "varying]::text[]))",
    "command_receipts.ck_command_receipts_entity_type": "CHECK (result_entity_type::text = ANY "
    "(ARRAY['employer'::character varying, "
    "'employer_contact'::character varying, "
    "'intake'::character varying, "
    "'work_interest'::character "
    "varying]::text[]))",
    "command_receipts.ck_command_receipts_result_authority_shape": "CHECK (command_type::text = "
    "'create_draft_employer'::text "
    "AND result_entity_type::text = "
    "'employer'::text AND "
    "result_event_type::text = "
    "'employer.created'::text AND "
    "result_record_version = 1 OR "
    "command_type::text = "
    "'create_employer_contact'::text "
    "AND result_entity_type::text = "
    "'employer_contact'::text AND "
    "result_event_type::text = "
    "'employer_contact.created'::text "
    "AND result_record_version = 1 "
    "OR command_type::text = "
    "'revise_draft_employer'::text "
    "AND result_entity_type::text = "
    "'employer'::text AND "
    "result_event_type::text = "
    "'employer.draft_revised'::text "
    "AND result_record_version >= 2 "
    "OR command_type::text = "
    "'create_intake'::text AND "
    "result_entity_type::text = "
    "'intake'::text AND "
    "result_event_type::text = "
    "'intake.created'::text AND "
    "result_record_version = 1 OR "
    "(command_type::text = ANY "
    "(ARRAY['revise_intake'::character "
    "varying, "
    "'revise_intake_address'::character "
    "varying]::text[])) AND "
    "result_entity_type::text = "
    "'intake'::text AND "
    "result_event_type::text = "
    "'intake.revised'::text AND "
    "result_record_version >= 2 OR "
    "command_type::text = "
    "'review_intake'::text AND "
    "result_entity_type::text = "
    "'intake'::text AND "
    "result_event_type::text = "
    "'intake.reviewed'::text AND "
    "result_record_version >= 2 OR "
    "command_type::text = "
    "'follow_up_intake'::text AND "
    "result_entity_type::text = "
    "'intake'::text AND "
    "result_event_type::text = "
    "'intake.follow_up_recorded'::text "
    "AND result_record_version >= 2 "
    "OR command_type::text = "
    "'create_work_interest'::text "
    "AND result_entity_type::text = "
    "'work_interest'::text AND "
    "result_event_type::text = "
    "'work_interest.created'::text "
    "AND result_record_version = 1 "
    "OR command_type::text = "
    "'revise_work_interest'::text "
    "AND result_entity_type::text = "
    "'work_interest'::text AND "
    "result_event_type::text = "
    "'work_interest.revised'::text "
    "AND result_record_version >= 2)",
    "command_receipts.fk_command_receipts_primary_result": "FOREIGN KEY (command_id, "
    "result_entity_type, result_entity_id, "
    "result_record_version, "
    "result_event_type, actor_id) REFERENCES "
    "command_results(command_id, "
    "entity_type, entity_id, result_version, "
    "event_type, actor_id) DEFERRABLE "
    "INITIALLY DEFERRED",
    "command_results.ck_command_results_authority_shape": "CHECK (command_type::text = "
    "'create_draft_employer'::text AND "
    "entity_type::text = 'employer'::text AND "
    "event_type::text = "
    "'employer.created'::text AND "
    "result_version = 1 OR command_type::text "
    "= 'create_employer_contact'::text AND "
    "entity_type::text = "
    "'employer_contact'::text AND "
    "event_type::text = "
    "'employer_contact.created'::text AND "
    "result_version = 1 OR command_type::text "
    "= 'revise_draft_employer'::text AND "
    "entity_type::text = 'employer'::text AND "
    "event_type::text = "
    "'employer.draft_revised'::text AND "
    "result_version >= 2 OR "
    "command_type::text = "
    "'create_intake'::text AND "
    "entity_type::text = 'intake'::text AND "
    "event_type::text = "
    "'intake.created'::text AND "
    "result_version = 1 OR "
    "(command_type::text = ANY "
    "(ARRAY['revise_intake'::character "
    "varying, "
    "'revise_intake_address'::character "
    "varying]::text[])) AND entity_type::text "
    "= 'intake'::text AND event_type::text = "
    "'intake.revised'::text AND "
    "result_version >= 2 OR "
    "command_type::text = "
    "'review_intake'::text AND "
    "entity_type::text = 'intake'::text AND "
    "event_type::text = "
    "'intake.reviewed'::text AND "
    "result_version >= 2 OR "
    "command_type::text = "
    "'follow_up_intake'::text AND "
    "entity_type::text = 'intake'::text AND "
    "event_type::text = "
    "'intake.follow_up_recorded'::text AND "
    "result_version >= 2 OR "
    "command_type::text = "
    "'create_work_interest'::text AND "
    "entity_type::text = "
    "'work_interest'::text AND "
    "event_type::text = "
    "'work_interest.created'::text AND "
    "result_version = 1 OR command_type::text "
    "= 'revise_work_interest'::text AND "
    "entity_type::text = "
    "'work_interest'::text AND "
    "event_type::text = "
    "'work_interest.revised'::text AND "
    "result_version >= 2)",
    "command_results.ck_command_results_version_positive": "CHECK (result_version >= 1)",
    "command_results.command_results_pkey": "PRIMARY KEY (command_id, entity_type, entity_id)",
    "command_results.fk_command_results_entity_authority": "FOREIGN KEY (entity_type, entity_id) "
    "REFERENCES "
    "entity_authorities(entity_type, "
    "entity_id) DEFERRABLE INITIALLY "
    "DEFERRED",
    "command_results.fk_command_results_exact_audit": "FOREIGN KEY (command_id, entity_id, "
    "result_version, event_type, actor_id) "
    "REFERENCES audit_events(command_id, "
    "entity_id, new_record_version, event_type, "
    "actor_id) DEFERRABLE INITIALLY DEFERRED",
    "command_results.fk_command_results_receipt_actor_type": "FOREIGN KEY (command_id, actor_id, "
    "command_type) REFERENCES "
    "command_receipts(command_id, "
    "actor_id, command_type) DEFERRABLE "
    "INITIALLY DEFERRED",
    "command_results.fk_command_results_typed_audit": "FOREIGN KEY (command_id, entity_type, "
    "entity_id) REFERENCES "
    "audit_events(command_id, entity_type, "
    "entity_id) DEFERRABLE INITIALLY DEFERRED",
    "command_results.uq_command_results_exact_authority": "UNIQUE (command_id, entity_type, "
    "entity_id, result_version, event_type, "
    "actor_id)",
    "command_results.uq_command_results_single_result": "UNIQUE (command_id)",
    "entity_authorities.ck_entity_authorities_entity_type": "CHECK (entity_type::text = ANY "
    "(ARRAY['employer'::character varying, "
    "'employer_contact'::character varying, "
    "'intake'::character varying, "
    "'work_interest'::character "
    "varying]::text[]))",
    "entity_authorities.ck_entity_authorities_exactly_one_concrete_id": "CHECK (entity_type::text = "
    "'employer'::text AND "
    "employer_id IS NOT NULL "
    "AND employer_id = "
    "entity_id AND "
    "employer_contact_id IS "
    "NULL AND intake_id IS NULL "
    "AND work_interest_id IS "
    "NULL OR entity_type::text "
    "= 'employer_contact'::text "
    "AND employer_contact_id IS "
    "NOT NULL AND "
    "employer_contact_id = "
    "entity_id AND employer_id "
    "IS NULL AND intake_id IS "
    "NULL AND work_interest_id "
    "IS NULL OR "
    "entity_type::text = "
    "'intake'::text AND "
    "intake_id IS NOT NULL AND "
    "intake_id = entity_id AND "
    "employer_id IS NULL AND "
    "employer_contact_id IS "
    "NULL AND work_interest_id "
    "IS NULL OR "
    "entity_type::text = "
    "'work_interest'::text AND "
    "work_interest_id IS NOT "
    "NULL AND work_interest_id "
    "= entity_id AND "
    "employer_id IS NULL AND "
    "employer_contact_id IS "
    "NULL AND intake_id IS "
    "NULL)",
    "entity_authorities.entity_authorities_work_interest_id_key": "UNIQUE (work_interest_id)",
    "entity_authorities.fk_entity_authorities_intake": "FOREIGN KEY (intake_id) REFERENCES "
    "intakes(intake_id) DEFERRABLE INITIALLY "
    "DEFERRED",
    "entity_authorities.fk_entity_authorities_work_interest": "FOREIGN KEY (work_interest_id) "
    "REFERENCES "
    "work_interests(interest_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "intake_addresses.ck_intake_addresses_country": "CHECK (country IS NULL OR country::text ~ "
    "'^[A-Z]{2}$'::text)",
    "intake_addresses.ck_intake_addresses_nonblank": "CHECK ((line1 IS NULL OR btrim(line1::text) "
    "<> ''::text) AND (line2 IS NULL OR "
    "btrim(line2::text) <> ''::text) AND (locality "
    "IS NULL OR btrim(locality::text) <> ''::text) "
    "AND (region IS NULL OR btrim(region::text) <> "
    "''::text) AND (postal_code IS NULL OR "
    "btrim(postal_code::text) <> ''::text))",
    "intake_addresses.ck_intake_addresses_section": "CHECK (section::text = ANY "
    "(ARRAY['worker_residence'::character varying, "
    "'party_address'::character varying, "
    "'worksite_address'::character "
    "varying]::text[]))",
    "intake_addresses.fk_intake_addresses_intake": "FOREIGN KEY (intake_id) REFERENCES "
    "intakes(intake_id)",
    "intake_addresses.guard_intake_address_authority": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "intake_addresses.intake_addresses_pkey": "PRIMARY KEY (intake_id, section)",
    "intake_follow_up_events.ck_intake_follow_up_shape": "CHECK (action::text = "
    "'needs_follow_up'::text AND review_id IS "
    "NOT NULL AND reason_code IS NOT NULL AND "
    "(reason_code::text = ANY "
    "(ARRAY['missing_information'::character "
    "varying, 'clarification'::character "
    "varying, 'other'::character "
    "varying]::text[])) AND method IS NULL AND "
    "outcome IS NULL OR (action::text = ANY "
    "(ARRAY['reschedule'::character varying, "
    "'reassign'::character varying]::text[])) "
    "AND review_id IS NULL AND reason_code IS "
    "NULL AND method IS NULL AND outcome IS "
    "NULL OR action::text = 'attempt'::text "
    "AND review_id IS NULL AND reason_code IS "
    "NULL AND method IS NOT NULL AND "
    "(method::text = ANY "
    "(ARRAY['phone'::character varying, "
    "'email'::character varying, "
    "'in_person'::character varying, "
    "'other'::character varying]::text[])) AND "
    "outcome IS NOT NULL AND (outcome::text = "
    "ANY (ARRAY['no_answer'::character "
    "varying, 'voicemail_left'::character "
    "varying, 'callback_requested'::character "
    "varying, "
    "'contact_reached_information_pending'::character "
    "varying, "
    "'invalid_contact_information'::character "
    "varying, "
    "'information_received'::character "
    "varying, 'other'::character "
    "varying]::text[])))",
    "intake_follow_up_events.fk_intake_follow_up_required_payload": "FOREIGN KEY (event_id) "
    "REFERENCES "
    "intake_history_payloads(event_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "intake_follow_up_events.guard_intake_workflow_authority": "TRIGGER DEFERRABLE INITIALLY "
    "DEFERRED",
    "intake_follow_up_events.intake_follow_up_events_action_check": "CHECK (action::text = ANY "
    "(ARRAY['needs_follow_up'::character "
    "varying, "
    "'reschedule'::character "
    "varying, 'reassign'::character "
    "varying, 'attempt'::character "
    "varying]::text[]))",
    "intake_follow_up_events.intake_follow_up_events_actor_display_name_check": "CHECK "
    "(btrim(actor_display_name::text) "
    "<> ''::text)",
    "intake_follow_up_events.intake_follow_up_events_check": "CHECK (content_version >= 1 AND "
    "content_version < version)",
    "intake_follow_up_events.intake_follow_up_events_command_id_fkey": "FOREIGN KEY (command_id) "
    "REFERENCES "
    "command_receipts(command_id) "
    "DEFERRABLE INITIALLY "
    "DEFERRED",
    "intake_follow_up_events.intake_follow_up_events_command_id_key": "UNIQUE (command_id)",
    "intake_follow_up_events.intake_follow_up_events_event_id_fkey": "FOREIGN KEY (event_id) "
    "REFERENCES "
    "audit_events(audit_event_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "intake_follow_up_events.intake_follow_up_events_intake_id_fkey": "FOREIGN KEY (intake_id) "
    "REFERENCES "
    "intakes(intake_id)",
    "intake_follow_up_events.intake_follow_up_events_intake_id_review_id_fkey": "FOREIGN KEY "
    "(intake_id, "
    "review_id) "
    "REFERENCES "
    "intake_reviews(intake_id, "
    "review_id) "
    "DEFERRABLE "
    "INITIALLY DEFERRED",
    "intake_follow_up_events.intake_follow_up_events_intake_id_version_key": "UNIQUE (intake_id, "
    "version)",
    "intake_follow_up_events.intake_follow_up_events_pkey": "PRIMARY KEY (event_id)",
    "intake_follow_up_events.intake_follow_up_events_time_zone_check": "CHECK "
    "(btrim(time_zone::text) <> "
    "''::text)",
    "intake_follow_up_events.intake_follow_up_events_version_check": "CHECK (version >= 2)",
    "intake_history_payloads.guard_intake_workflow_authority": "TRIGGER DEFERRABLE INITIALLY "
    "DEFERRED",
    "intake_history_payloads.intake_history_payloads_event_id_fkey": "FOREIGN KEY (event_id) "
    "REFERENCES "
    "intake_follow_up_events(event_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "intake_history_payloads.intake_history_payloads_note_check": "CHECK (note IS NULL OR "
    "btrim(note::text) <> ''::text)",
    "intake_history_payloads.intake_history_payloads_pkey": "PRIMARY KEY (event_id)",
    "intake_history_payloads.intake_history_payloads_reason_text_check": "CHECK "
    "(btrim(reason_text::text) "
    "<> ''::text)",
    "intake_links.ck_intake_links_not_available": "CHECK (false)",
    "intake_links.fk_intake_links_intake": "FOREIGN KEY (intake_id) REFERENCES intakes(intake_id)",
    "intake_links.intake_links_pkey": "PRIMARY KEY (intake_id)",
    "intake_review_payloads.guard_intake_workflow_authority": "TRIGGER DEFERRABLE INITIALLY "
    "DEFERRED",
    "intake_review_payloads.intake_review_payloads_dependency_refs_check": "CHECK (dependency_refs "
    "= '{}'::jsonb)",
    "intake_review_payloads.intake_review_payloads_note_check": "CHECK (note IS NULL OR "
    "btrim(note::text) <> ''::text)",
    "intake_review_payloads.intake_review_payloads_pkey": "PRIMARY KEY (review_id)",
    "intake_review_payloads.intake_review_payloads_review_id_fkey": "FOREIGN KEY (review_id) "
    "REFERENCES "
    "intake_reviews(review_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "intake_review_payloads.intake_review_payloads_reviewed_content_check": "CHECK "
    "(jsonb_typeof(reviewed_content) "
    "= 'object'::text)",
    "intake_reviews.fk_intake_reviews_required_payload": "FOREIGN KEY (review_id) REFERENCES "
    "intake_review_payloads(review_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "intake_reviews.guard_intake_workflow_authority": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "intake_reviews.intake_reviews_actor_display_name_check": "CHECK "
    "(btrim(actor_display_name::text) <> "
    "''::text)",
    "intake_reviews.intake_reviews_check": "CHECK (reviewed_content_version >= 1 AND "
    "reviewed_content_version <= reviewed_record_version)",
    "intake_reviews.intake_reviews_check1": "CHECK (result_version = (reviewed_record_version + 1))",
    "intake_reviews.intake_reviews_command_id_fkey": "FOREIGN KEY (command_id) REFERENCES "
    "command_receipts(command_id) DEFERRABLE "
    "INITIALLY DEFERRED",
    "intake_reviews.intake_reviews_command_id_key": "UNIQUE (command_id)",
    "intake_reviews.intake_reviews_event_id_fkey": "FOREIGN KEY (event_id) REFERENCES "
    "audit_events(audit_event_id) DEFERRABLE "
    "INITIALLY DEFERRED",
    "intake_reviews.intake_reviews_event_id_key": "UNIQUE (event_id)",
    "intake_reviews.intake_reviews_intake_id_fkey": "FOREIGN KEY (intake_id) REFERENCES "
    "intakes(intake_id)",
    "intake_reviews.intake_reviews_intake_id_result_version_key": "UNIQUE (intake_id, "
    "result_version)",
    "intake_reviews.intake_reviews_intake_id_review_id_key": "UNIQUE (intake_id, review_id)",
    "intake_reviews.intake_reviews_outcome_check": "CHECK (outcome::text = ANY "
    "(ARRAY['intake_reviewed'::character varying, "
    "'needs_follow_up'::character varying]::text[]))",
    "intake_reviews.intake_reviews_pkey": "PRIMARY KEY (review_id)",
    "intake_reviews.intake_reviews_reviewed_record_version_check": "CHECK (reviewed_record_version "
    ">= 1)",
    "intakes.ck_intakes_content_kind": "CHECK (kind::text = 'worker'::text AND (content - "
    "ARRAY['full_name'::text, 'phone'::text, 'interests'::text, "
    "'availability'::text]) = '{}'::jsonb OR kind::text = "
    "'employer'::text AND (content - "
    "ARRAY['employer_type'::text, 'display_name'::text, "
    "'representative_name'::text, 'phone'::text, "
    "'role_title'::text, 'duties_summary'::text, "
    "'worker_count'::text, 'schedule'::text, 'offer'::text]) = "
    "'{}'::jsonb)",
    "intakes.ck_intakes_content_object": "CHECK (jsonb_typeof(content) = 'object'::text)",
    "intakes.ck_intakes_content_size": "CHECK (octet_length(content::text) <= 32768)",
    "intakes.ck_intakes_content_version": "CHECK (content_version >= 1 AND content_version <= "
    "version)",
    "intakes.ck_intakes_kind": "CHECK (kind::text = ANY (ARRAY['worker'::character varying, "
    "'employer'::character varying]::text[]))",
    "intakes.ck_intakes_lifecycle_draft": "CHECK (lifecycle_status::text = 'draft'::text)",
    "intakes.ck_intakes_schema_version": "CHECK (schema_version = 1)",
    "intakes.ck_intakes_version_positive": "CHECK (version >= 1)",
    "intakes.guard_intake_write_authority": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "intakes.intakes_pkey": "PRIMARY KEY (intake_id)",
    "intakes.uq_intakes_id_kind": "UNIQUE (intake_id, kind)",
    "work_interest_versions.guard_work_interest_authority": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "work_interest_versions.work_interest_versions_command_id_fkey": "FOREIGN KEY (command_id) "
    "REFERENCES "
    "command_receipts(command_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "work_interest_versions.work_interest_versions_command_id_key": "UNIQUE (command_id)",
    "work_interest_versions.work_interest_versions_interest_id_fkey": "FOREIGN KEY (interest_id) "
    "REFERENCES "
    "work_interests(interest_id)",
    "work_interest_versions.work_interest_versions_label_en_check": "CHECK (btrim(label_en::text) "
    "<> ''::text)",
    "work_interest_versions.work_interest_versions_label_es_check": "CHECK (btrim(label_es::text) "
    "<> ''::text)",
    "work_interest_versions.work_interest_versions_pkey": "PRIMARY KEY (interest_id, version)",
    "work_interest_versions.work_interest_versions_version_check": "CHECK (version >= 1)",
    "work_interests.ck_work_interests_code": "CHECK (code::text ~ '^[a-z0-9_]{1,64}$'::text)",
    "work_interests.guard_work_interest_authority": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "work_interests.work_interests_code_key": "UNIQUE (code)",
    "work_interests.work_interests_label_en_check": "CHECK (btrim(label_en::text) <> ''::text)",
    "work_interests.work_interests_label_es_check": "CHECK (btrim(label_es::text) <> ''::text)",
    "work_interests.work_interests_pkey": "PRIMARY KEY (interest_id)",
    "work_interests.work_interests_version_check": "CHECK (version >= 1)",
}

INTAKE_CONSTRAINT_QUERY = text("""
    SELECT t.relname||'.'||c.conname AS key,
      pg_get_constraintdef(c.oid,true) AS definition, c.convalidated
    FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid
    JOIN pg_namespace n ON n.oid=t.relnamespace
    WHERE n.nspname='public' AND t.relname||'.'||c.conname = ANY(:names)
""")

RUNTIME_COLUMN_UPDATE_QUERY = text("""
    SELECT c.relname AS table_name, a.attname AS column_name,
      has_column_privilege(:runtime_role,c.oid,a.attnum,'UPDATE') AS allowed
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    JOIN pg_attribute a ON a.attrelid=c.oid
    WHERE n.nspname='public' AND c.relname = ANY(:table_names)
      AND a.attnum>0 AND NOT a.attisdropped
""")
INTAKE_TRIGGER_QUERY = text("""
    SELECT c.relname AS table_name,t.tgname AS trigger_name,t.tgenabled,
      t.tgdeferrable,t.tginitdeferred,p.proname AS function_name
    FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
    JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_proc p ON p.oid=t.tgfoid
    WHERE n.nspname='public' AND NOT t.tgisinternal
      AND (c.relname = ANY(:table_names) OR t.tgname IN ('populate_legacy_command_result','guard_intake_workflow_authority','guard_work_interest_authority'))
""")
EXPECTED_INTAKE_TRIGGERS = {
    "audit_events.guard_intake_workflow_authority": ("guard_intake_workflow_authority", True),
    "audit_events.guard_work_interest_authority": ("guard_work_interest_authority", True),
    "command_receipts.populate_legacy_command_result": ("populate_legacy_command_result", False),
    "command_results.deny_mutation_command_results": ("deny_mutation_on_append_only_tables", False),
    "intake_addresses.deny_mutation_intake_addresses": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "intake_addresses.guard_intake_address_authority": ("guard_intake_address_authority", True),
    "intake_addresses.guard_intake_address_identity": ("guard_intake_identity", False),
    "intake_follow_up_events.deny_mutation_intake_follow_up_events": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "intake_follow_up_events.guard_intake_workflow_authority": (
        "guard_intake_workflow_authority",
        True,
    ),
    "intake_history_payloads.deny_mutation_intake_history_payloads": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "intake_history_payloads.guard_intake_workflow_authority": (
        "guard_intake_workflow_authority",
        True,
    ),
    "intake_links.deny_mutation_intake_links": ("deny_mutation_on_append_only_tables", False),
    "intake_review_payloads.deny_mutation_intake_review_payloads": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "intake_review_payloads.guard_intake_workflow_authority": (
        "guard_intake_workflow_authority",
        True,
    ),
    "intake_reviews.deny_mutation_intake_reviews": ("deny_mutation_on_append_only_tables", False),
    "intake_reviews.guard_intake_workflow_authority": ("guard_intake_workflow_authority", True),
    "intakes.deny_mutation_intakes": ("deny_mutation_on_append_only_tables", False),
    "intakes.guard_intake_identity": ("guard_intake_identity", False),
    "intakes.guard_intake_write_authority": ("guard_intake_write_authority", True),
    "work_interest_versions.deny_mutation_work_interest_versions": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "work_interest_versions.guard_work_interest_authority": ("guard_work_interest_authority", True),
    "work_interests.deny_mutation_work_interests": ("deny_mutation_on_append_only_tables", False),
    "work_interests.guard_work_interest_authority": ("guard_work_interest_authority", True),
    "work_interests.guard_work_interest_identity": ("guard_work_interest_identity", False),
}


def _as_set(values: object) -> set[str]:
    if not isinstance(values, Iterable) or isinstance(values, (str, bytes, dict)):
        return set()
    return {str(value) for value in values}


def _role_attributes(
    connection: Connection, role_names: Iterable[str]
) -> dict[str, dict[str, object]]:
    normalized = sorted({role_name for role_name in role_names if role_name})
    if not normalized:
        return {}
    return {
        row["rolname"]: {
            "rolcanlogin": row["rolcanlogin"],
            "rolsuper": row["rolsuper"],
            "rolcreaterole": row["rolcreaterole"],
            "rolcreatedb": row["rolcreatedb"],
            "rolreplication": row["rolreplication"],
            "rolbypassrls": row["rolbypassrls"],
            "rolinherit": row["rolinherit"],
        }
        for row in connection.execute(
            ROLE_ATTRIBUTES_QUERY,
            {"role_names": normalized},
        ).mappings()
    }


def _role_memberships(connection: Connection, role_names: Iterable[str]) -> dict[str, list[str]]:
    normalized = sorted({role_name for role_name in role_names if role_name})
    memberships: dict[str, list[str]] = {role_name: [] for role_name in normalized}
    if not normalized:
        return memberships
    for row in connection.execute(
        ROLE_MEMBERSHIP_QUERY,
        {"role_names": normalized},
    ).mappings():
        memberships.setdefault(str(row["member"]), []).append(str(row["granted"]))
    return memberships


def collect_authority_snapshot(
    connection: Connection,
    *,
    migration_login_role: str | None = None,
    runtime_login_role: str | None = None,
) -> dict[str, object]:
    governed_roles = [SCHEMA_OWNER_ROLE, MIGRATOR_ROLE, RUNTIME_ROLE]
    authenticated_roles = [
        role_name
        for role_name in (migration_login_role, runtime_login_role)
        if role_name is not None
    ]
    roles = _role_attributes(
        connection, [*governed_roles, *authenticated_roles, "cloudsqlsuperuser"]
    )
    authority_memberships = [
        dict(row)
        for row in connection.execute(
            AUTHORITY_MEMBERSHIP_QUERY,
            {"role_names": [*governed_roles, *authenticated_roles]},
        ).mappings()
    ]
    if "cloudsqlsuperuser" not in roles:
        local_members = [
            str(row["member"]) for row in authority_memberships if row["granted"] == MIGRATOR_ROLE
        ]
        roles.update(_role_attributes(connection, local_members))
    role_memberships = _role_memberships(connection, governed_roles)
    authenticated_role_memberships = _role_memberships(connection, authenticated_roles)

    schema_owner = connection.execute(SCHEMA_OWNER_QUERY).scalar_one()
    table_owners = {
        row["object_name"]: row["owner"] for row in connection.execute(TABLE_OWNER_QUERY).mappings()
    }
    function_owners = {
        row["object_name"]: row["owner"]
        for row in connection.execute(
            FUNCTION_OWNER_QUERY,
            {"function_names": sorted(EXPECTED_SCHEMA_OWNER_FUNCTIONS)},
        ).mappings()
    }
    public_table_privileges: dict[str, list[str]] = defaultdict(list)
    for row in connection.execute(PUBLIC_TABLE_PRIVILEGE_QUERY).mappings():
        public_table_privileges[str(row["table_name"])].append(str(row["privilege_type"]))

    runtime_table_privileges: dict[str, list[str]] = defaultdict(list)
    for row in connection.execute(
        RUNTIME_TABLE_PRIVILEGE_QUERY,
        {"runtime_role": RUNTIME_ROLE},
    ).mappings():
        if row["allowed"]:
            runtime_table_privileges[str(row["table_name"])].append(str(row["privilege_type"]))

    runtime_schema_privileges = [
        str(row["privilege_type"])
        for row in connection.execute(
            RUNTIME_SCHEMA_PRIVILEGE_QUERY,
            {"runtime_role": RUNTIME_ROLE},
        ).mappings()
        if row["allowed"]
    ]

    runtime_function_privileges: dict[str, list[str]] = defaultdict(list)
    for row in connection.execute(
        RUNTIME_FUNCTION_PRIVILEGE_QUERY,
        {"runtime_role": RUNTIME_ROLE},
    ).mappings():
        if row["allowed"]:
            runtime_function_privileges[str(row["function_name"])].append("EXECUTE")

    default_privileges: dict[str, list[str]] = {name: [] for name in EXPECTED_DEFAULT_PRIVILEGES}
    public_default_privileges: dict[str, list[str]] = {
        name: [] for name in EXPECTED_PUBLIC_DEFAULT_PRIVILEGES
    }
    for row in connection.execute(
        DEFAULT_PRIVILEGE_QUERY,
        {"schema_owner": SCHEMA_OWNER_ROLE},
    ).mappings():
        grantee = row["grantee"]
        privilege_type = row["privilege_type"]
        if grantee is None or privilege_type is None:
            continue
        object_type = DEFAULT_PRIVILEGE_OBJECT_TYPE_MAP.get(str(row["objtype"]))
        if object_type is None:
            continue
        if grantee == RUNTIME_ROLE:
            default_privileges[object_type].append(str(privilege_type))
        if grantee == PUBLIC_ROLE:
            public_default_privileges[object_type].append(str(privilege_type))

    intake_constraints = {
        row["key"]: row["definition"] if row["convalidated"] else None
        for row in connection.execute(
            INTAKE_CONSTRAINT_QUERY, {"names": list(EXPECTED_INTAKE_CONSTRAINTS)}
        ).mappings()
    }
    runtime_update_columns: dict[str, list[str]] = defaultdict(list)
    for row in connection.execute(
        RUNTIME_COLUMN_UPDATE_QUERY,
        {
            "runtime_role": RUNTIME_ROLE,
            "table_names": list(EXPECTED_RUNTIME_UPDATE_COLUMNS),
        },
    ).mappings():
        if row["allowed"]:
            runtime_update_columns[row["table_name"]].append(row["column_name"])
    intake_triggers = {
        f"{row['table_name']}.{row['trigger_name']}": {
            "function": row["function_name"],
            "enabled": row["tgenabled"],
            "deferred": row["tgdeferrable"] and row["tginitdeferred"],
        }
        for row in connection.execute(
            INTAKE_TRIGGER_QUERY,
            {
                "table_names": list(EXPECTED_RUNTIME_UPDATE_COLUMNS),
            },
        ).mappings()
    }
    security_definer_functions = (
        connection.execute(
            text("""
        SELECT p.proname FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
        WHERE n.nspname='public' AND p.proname=ANY(:names) AND p.prosecdef
    """),
            {"names": list(EXPECTED_SCHEMA_OWNER_FUNCTIONS)},
        )
        .scalars()
        .all()
    )

    return {
        "intake_constraints": intake_constraints,
        "runtime_update_columns": dict(runtime_update_columns),
        "intake_triggers": intake_triggers,
        "security_definer_functions": security_definer_functions,
        "roles": roles,
        "authority_memberships": authority_memberships,
        "schema_owner": schema_owner,
        "role_memberships": role_memberships,
        "authenticated_role_memberships": authenticated_role_memberships,
        "migration_login_role": migration_login_role,
        "runtime_login_role": runtime_login_role,
        "table_owners": table_owners,
        "function_owners": function_owners,
        "public_table_privileges": dict(public_table_privileges),
        "runtime_table_privileges": dict(runtime_table_privileges),
        "runtime_schema_privileges": runtime_schema_privileges,
        "runtime_function_privileges": dict(runtime_function_privileges),
        "default_privileges": default_privileges,
        "public_default_privileges": public_default_privileges,
    }


def _evaluate_membership_graph(
    snapshot: dict[str, object], roles: dict[str, dict[str, object]]
) -> list[str]:
    rows = snapshot.get("authority_memberships")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        return ["snapshot missing structured authority memberships"]
    # This verifier admits complete local and managed catalog shapes. Bootstrap selection is
    # separately restricted to the explicit managed deployment target.
    managed = "cloudsqlsuperuser" in roles
    native = managed and not any(row.get("member") == "cloudsqlsuperuser" for row in rows)
    expected_edges = {
        (MIGRATOR_ROLE, SCHEMA_OWNER_ROLE),
        (snapshot.get("migration_login_role"), MIGRATOR_ROLE),
        (snapshot.get("runtime_login_role"), RUNTIME_ROLE),
    }
    admin_edges = (
        {("cloudsqlsuperuser", role) for role in (SCHEMA_OWNER_ROLE, MIGRATOR_ROLE, RUNTIME_ROLE)}
        if managed and not native
        else set()
    )
    seen: set[tuple[object, object]] = set()
    violations = []
    if managed and roles["cloudsqlsuperuser"] != {
        "rolcanlogin": True,
        "rolinherit": True,
        "rolcreatedb": True,
        "rolcreaterole": True,
        "rolsuper": False,
        "rolreplication": False,
        "rolbypassrls": False,
    }:
        violations.append("managed database grantor attributes drifted")
    if native and (
        any(
            row.get("grantor_superuser") is not True
            or not isinstance(row.get("grantor"), str)
            or not row.get("grantor")
            for row in rows
        )
        or len({row.get("grantor") for row in rows if isinstance(row.get("grantor"), str)}) != 1
    ):
        violations.append("native managed memberships must share one durable superuser grantor")
    for row in rows:
        edge = (row.get("member"), row.get("granted"))
        options = (row.get("admin_option"), row.get("inherit_option"), row.get("set_option"))
        if edge in seen:
            violations.append("duplicate authority membership")
        seen.add(edge)
        if edge in admin_edges:
            if options != (True, False, False) or row.get("grantor_superuser") is not True:
                violations.append("managed creator membership drifted")
        elif edge in expected_edges:
            if options != (False, True, True):
                violations.append("restricted authority membership options drifted")
            if (
                managed
                and not native
                and edge == (MIGRATOR_ROLE, SCHEMA_OWNER_ROLE)
                and row.get("grantor") != "cloudsqlsuperuser"
            ):
                violations.append("schema owner membership must use durable managed grantor")
        elif (
            not managed
            and row.get("member") in roles
            and roles[row["member"]].get("rolsuper") is True
        ):
            # Local test installations may retain their actual superuser grant.
            if edge[1] != MIGRATOR_ROLE or options != (False, True, True):
                violations.append("unexpected local superuser membership")
        else:
            violations.append("unexpected incoming or outgoing authority membership")
    if not (expected_edges | admin_edges).issubset(seen):
        violations.append("missing expected authority membership")
    return violations


def evaluate_authority_snapshot(snapshot: dict[str, object]) -> list[str]:
    violations: list[str] = []

    constraints = snapshot.get("intake_constraints")
    if not isinstance(constraints, dict):
        violations.append("snapshot missing intake constraint definitions")
    else:
        for key, definition in EXPECTED_INTAKE_CONSTRAINTS.items():
            if constraints.get(key) != definition:
                violations.append(f"intake constraint drifted for {key}")
    update_columns = snapshot.get("runtime_update_columns")
    if not isinstance(update_columns, dict):
        violations.append("snapshot missing intake column privileges")
    else:
        for table, expected in EXPECTED_RUNTIME_UPDATE_COLUMNS.items():
            if _as_set(update_columns.get(table, [])) != expected:
                violations.append(f"runtime UPDATE columns drifted for {table}")
    triggers = snapshot.get("intake_triggers")
    if not isinstance(triggers, dict):
        violations.append("snapshot missing intake triggers")
    else:
        for key, (function, deferred) in EXPECTED_INTAKE_TRIGGERS.items():
            if triggers.get(key) != {"function": function, "enabled": "O", "deferred": deferred}:
                violations.append(f"intake trigger drifted for {key}")
    if snapshot.get("security_definer_functions") != []:
        violations.append("governed functions must use invoker authority")

    roles = snapshot.get("roles")
    if not isinstance(roles, dict):
        return ["snapshot missing roles"]
    violations.extend(_evaluate_membership_graph(snapshot, roles))
    for role_name in (
        SCHEMA_OWNER_ROLE,
        MIGRATOR_ROLE,
        RUNTIME_ROLE,
        snapshot.get("migration_login_role"),
        snapshot.get("runtime_login_role"),
    ):
        role = roles.get(role_name)
        if not isinstance(role, dict):
            continue
        for attribute in ("rolcreatedb", "rolreplication", "rolbypassrls"):
            if role.get(attribute) is not False:
                violations.append(f"role {role_name} must not have {attribute}")
        if role.get("rolinherit") is not True:
            violations.append(f"role {role_name} must inherit its restricted role")
    for role_name in (SCHEMA_OWNER_ROLE, MIGRATOR_ROLE, RUNTIME_ROLE):
        role = roles.get(role_name)
        if not isinstance(role, dict):
            violations.append(f"missing role {role_name}")
            continue
        if role.get("rolcanlogin") is not False:
            violations.append(f"role {role_name} must be NOLOGIN")
        if role.get("rolsuper") is not False:
            violations.append(f"role {role_name} must not be superuser")
        if role.get("rolcreaterole") is not False:
            violations.append(f"role {role_name} must not manage roles")

    if snapshot.get("schema_owner") != SCHEMA_OWNER_ROLE:
        violations.append("public schema owner drifted from golden_rose_schema_owner")

    role_memberships = snapshot.get("role_memberships")
    if not isinstance(role_memberships, dict):
        violations.append("snapshot missing role memberships")
    else:
        migrator_memberships = _as_set(role_memberships.get(MIGRATOR_ROLE, []))
        if migrator_memberships != {SCHEMA_OWNER_ROLE}:
            violations.append("golden_rose_migrator must assume only golden_rose_schema_owner")
        runtime_memberships = _as_set(role_memberships.get(RUNTIME_ROLE, []))
        if runtime_memberships:
            violations.append("golden_rose_runtime must not inherit privileged roles")

    authenticated_role_memberships = snapshot.get("authenticated_role_memberships")
    if authenticated_role_memberships is not None and not isinstance(
        authenticated_role_memberships, dict
    ):
        violations.append("snapshot missing authenticated role memberships")
    elif isinstance(authenticated_role_memberships, dict):
        migration_login_role = snapshot.get("migration_login_role")
        runtime_login_role = snapshot.get("runtime_login_role")
        if isinstance(migration_login_role, str):
            migration_login = roles.get(migration_login_role)
            if not isinstance(migration_login, dict):
                violations.append(
                    f"missing authenticated migration login role {migration_login_role}"
                )
            else:
                if migration_login.get("rolcanlogin") is not True:
                    violations.append(
                        f"authenticated migration login role {migration_login_role} must be LOGIN"
                    )
                if migration_login.get("rolsuper") is not False:
                    violations.append(
                        f"authenticated migration login role {migration_login_role} must not be superuser"
                    )
                if migration_login.get("rolcreaterole") is not False:
                    violations.append(
                        f"authenticated migration login role {migration_login_role} must not manage roles"
                    )
            if _as_set(authenticated_role_memberships.get(migration_login_role, [])) != {
                MIGRATOR_ROLE
            }:
                violations.append(
                    f"authenticated migration login role {migration_login_role} must inherit only {MIGRATOR_ROLE}"
                )
        if isinstance(runtime_login_role, str):
            runtime_login = roles.get(runtime_login_role)
            if not isinstance(runtime_login, dict):
                violations.append(f"missing authenticated runtime login role {runtime_login_role}")
            else:
                if runtime_login.get("rolcanlogin") is not True:
                    violations.append(
                        f"authenticated runtime login role {runtime_login_role} must be LOGIN"
                    )
                if runtime_login.get("rolsuper") is not False:
                    violations.append(
                        f"authenticated runtime login role {runtime_login_role} must not be superuser"
                    )
                if runtime_login.get("rolcreaterole") is not False:
                    violations.append(
                        f"authenticated runtime login role {runtime_login_role} must not manage roles"
                    )
            if _as_set(authenticated_role_memberships.get(runtime_login_role, [])) != {
                RUNTIME_ROLE
            }:
                violations.append(
                    f"authenticated runtime login role {runtime_login_role} must inherit only {RUNTIME_ROLE}"
                )

    table_owners = snapshot.get("table_owners")
    if not isinstance(table_owners, dict):
        violations.append("snapshot missing table owners")
    else:
        for object_name in EXPECTED_SCHEMA_OWNER_OBJECTS:
            if table_owners.get(object_name) != SCHEMA_OWNER_ROLE:
                violations.append(f"{object_name} owner drifted from {SCHEMA_OWNER_ROLE}")

    function_owners = snapshot.get("function_owners")
    if not isinstance(function_owners, dict):
        violations.append("snapshot missing function owners")
    else:
        for object_name in EXPECTED_SCHEMA_OWNER_FUNCTIONS:
            if function_owners.get(object_name) != SCHEMA_OWNER_ROLE:
                violations.append(f"{object_name} function owner drifted from {SCHEMA_OWNER_ROLE}")

    public_table_privileges = snapshot.get("public_table_privileges")
    if not isinstance(public_table_privileges, dict):
        violations.append("snapshot missing direct PUBLIC table privileges")
    else:
        for table_name, privileges in public_table_privileges.items():
            actual_privileges = _as_set(privileges)
            if actual_privileges:
                violations.append(
                    f"direct PUBLIC table privileges detected for {table_name}: "
                    f"{sorted(actual_privileges)}"
                )

    runtime_table_privileges = snapshot.get("runtime_table_privileges")
    if not isinstance(runtime_table_privileges, dict):
        violations.append("snapshot missing runtime table privileges")
    else:
        for table_name, expected_privileges in EXPECTED_RUNTIME_TABLE_PRIVILEGES.items():
            actual_privileges = _as_set(runtime_table_privileges.get(table_name, []))
            if actual_privileges != expected_privileges:
                violations.append(
                    f"runtime table privileges drifted for {table_name}: "
                    f"expected {sorted(expected_privileges)} got {sorted(actual_privileges)}"
                )

    runtime_schema_privileges = _as_set(snapshot.get("runtime_schema_privileges", []))
    if runtime_schema_privileges != EXPECTED_RUNTIME_SCHEMA_PRIVILEGES:
        violations.append(
            "runtime schema privileges drifted: "
            f"expected {sorted(EXPECTED_RUNTIME_SCHEMA_PRIVILEGES)} got {sorted(runtime_schema_privileges)}"
        )

    runtime_function_privileges = snapshot.get("runtime_function_privileges")
    if not isinstance(runtime_function_privileges, dict):
        violations.append("snapshot missing runtime function privileges")
    else:
        for function_name, expected_privileges in EXPECTED_RUNTIME_FUNCTION_PRIVILEGES.items():
            actual_privileges = _as_set(runtime_function_privileges.get(function_name, []))
            if actual_privileges != expected_privileges:
                violations.append(
                    f"runtime function privileges drifted for {function_name}: "
                    f"expected {sorted(expected_privileges)} got {sorted(actual_privileges)}"
                )

    default_privileges = snapshot.get("default_privileges")
    if not isinstance(default_privileges, dict):
        violations.append("snapshot missing default privileges")
    else:
        for object_type, expected_privileges in EXPECTED_DEFAULT_PRIVILEGES.items():
            actual_privileges = _as_set(default_privileges.get(object_type, []))
            if actual_privileges != expected_privileges:
                violations.append(
                    f"default {object_type} privileges drifted: "
                    f"expected {sorted(expected_privileges)} got {sorted(actual_privileges)}"
                )

    public_default_privileges = snapshot.get("public_default_privileges")
    if not isinstance(public_default_privileges, dict):
        violations.append("snapshot missing public default privileges")
    else:
        for object_type, expected_privileges in EXPECTED_PUBLIC_DEFAULT_PRIVILEGES.items():
            actual_privileges = _as_set(public_default_privileges.get(object_type, []))
            if actual_privileges != expected_privileges:
                violations.append(
                    f"public default {object_type} privileges drifted: "
                    f"expected {sorted(expected_privileges)} got {sorted(actual_privileges)}"
                )

    return violations


def _probe_denied(connection: Connection, statement: str, error_message: str) -> str | None:
    nested = connection.begin_nested()
    try:
        connection.execute(text(statement))
    except SQLAlchemyError:
        return None
    finally:
        with suppress(SQLAlchemyError):
            nested.rollback()
    return error_message


def probe_runtime_login(database_url: str) -> tuple[str, list[str]]:
    engine = create_engine(database_url, future=True)
    violations: list[str] = []
    try:
        with engine.connect() as connection:
            session_user = str(connection.execute(text("SELECT SESSION_USER")).scalar_one())
            current_user = str(connection.execute(text("SELECT CURRENT_USER")).scalar_one())
            if session_user != current_user:
                violations.append(
                    f"runtime login {session_user} must not start by assuming another role; current_user={current_user}"
                )
            if (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                is None
            ):
                violations.append(f"runtime login {session_user} cannot read alembic_version")
            for statement, error_message in (
                (
                    f"SET ROLE {SCHEMA_OWNER_ROLE}",
                    f"runtime login {session_user} can assume schema owner",
                ),
                (
                    "TRUNCATE TABLE command_receipts",
                    f"runtime login {session_user} can truncate append-only tables",
                ),
                (
                    "CREATE TABLE public.runtime_authority_probe(id integer)",
                    f"runtime login {session_user} can execute DDL in public schema",
                ),
                (
                    "ALTER TABLE audit_events DISABLE TRIGGER ALL",
                    f"runtime login {session_user} can disable audit triggers",
                ),
                (
                    f"GRANT {SCHEMA_OWNER_ROLE} TO {RUNTIME_ROLE}",
                    f"runtime login {session_user} can manage roles",
                ),
            ):
                violation = _probe_denied(connection, statement, error_message)
                if violation is not None:
                    violations.append(violation)
            return session_user, violations
    finally:
        engine.dispose()


def probe_migration_login(database_url: str) -> tuple[str, list[str]]:
    engine = create_engine(database_url, future=True)
    violations: list[str] = []
    try:
        with engine.connect() as connection:
            session_user = str(connection.execute(text("SELECT SESSION_USER")).scalar_one())
            before_current_user = str(connection.execute(text("SELECT CURRENT_USER")).scalar_one())
            if before_current_user != session_user:
                violations.append(
                    f"migration login {session_user} must begin as its authenticated login; current_user={before_current_user}"
                )
            nested = connection.begin_nested()
            try:
                connection.execute(text(f"SET ROLE {SCHEMA_OWNER_ROLE}"))
                assumed_user = str(connection.execute(text("SELECT CURRENT_USER")).scalar_one())
                if assumed_user != SCHEMA_OWNER_ROLE:
                    violations.append(
                        f"migration login {session_user} did not assume {SCHEMA_OWNER_ROLE}; current_user={assumed_user}"
                    )
            except SQLAlchemyError as exc:
                violations.append(
                    f"migration login {session_user} cannot assume {SCHEMA_OWNER_ROLE}: {exc.__class__.__name__}"
                )
            finally:
                with suppress(SQLAlchemyError):
                    nested.rollback()
            return session_user, violations
    finally:
        engine.dispose()


def _required_authenticated_probe_urls() -> tuple[str, str]:
    runtime_login_database_url = os.environ.get("GOLDEN_ROSE_RUNTIME_DATABASE_URL")
    migration_login_database_url = os.environ.get("GOLDEN_ROSE_MIGRATION_DATABASE_URL")
    missing = []
    if not runtime_login_database_url:
        missing.append("GOLDEN_ROSE_RUNTIME_DATABASE_URL")
    if not migration_login_database_url:
        missing.append("GOLDEN_ROSE_MIGRATION_DATABASE_URL")
    if missing:
        raise ValueError(
            "full database authority verification requires authenticated login probe URLs: "
            + ", ".join(missing)
        )
    assert runtime_login_database_url is not None
    assert migration_login_database_url is not None
    return runtime_login_database_url, migration_login_database_url


def identify_database(database_url: str) -> tuple[str, str, int]:
    engine = create_engine(database_url, future=True)
    try:
        with engine.connect() as connection:
            row = connection.execute(DATABASE_IDENTITY_QUERY).one()
            return (str(row.database_name), str(row.server_addr), int(row.server_port))
    finally:
        engine.dispose()


def validate_database_identities(identities: dict[str, tuple[str, str, int]]) -> list[str]:
    if len(set(identities.values())) == 1:
        return []
    rendered = ", ".join(f"{label}={identity!r}" for label, identity in sorted(identities.items()))
    return [f"database authority evidence must come from one database identity: {rendered}"]


def main() -> int:
    try:
        runtime_login_database_url, migration_login_database_url = (
            _required_authenticated_probe_urls()
        )
        probe_violations: list[str] = []
        authority_database_url = get_database_url()
        probe_violations.extend(
            validate_database_identities(
                {
                    "authority": identify_database(authority_database_url),
                    "migration": identify_database(migration_login_database_url),
                    "runtime": identify_database(runtime_login_database_url),
                }
            )
        )

        runtime_login_role, runtime_probe_violations = probe_runtime_login(
            runtime_login_database_url
        )
        probe_violations.extend(runtime_probe_violations)
        migration_login_role, migration_probe_violations = probe_migration_login(
            migration_login_database_url
        )
        probe_violations.extend(migration_probe_violations)

        engine = create_engine(authority_database_url, future=True)
        try:
            with engine.connect() as connection:
                snapshot = collect_authority_snapshot(
                    connection,
                    migration_login_role=migration_login_role,
                    runtime_login_role=runtime_login_role,
                )
        finally:
            engine.dispose()
    except ValueError as exc:
        print("database authority verification failed")
        print(f"- {exc}")
        return 1
    except SQLAlchemyError:
        print("database authority verification failed")
        print("- database connection boundary failed")
        return 1

    violations = [
        *evaluate_authority_snapshot(snapshot),
        *probe_violations,
    ]
    if violations:
        print("database authority verification failed")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("database authority verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
