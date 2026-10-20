# ruff: noqa: E501
"""Add optional email facts to worker and employer contact records."""

import importlib.util
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "0020_contact_email_fields"
down_revision = "0019_ext_calendar_imports"
branch_labels = None
depends_on = None


def execute(sql: str) -> None:
    op.execute(sa.text(sql))


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + ".py"))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Missing applied migration {name}")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def replace_function(sql: str) -> str:
    return sql.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1)


def correction_section_function(specs: dict[str, tuple[str, str, tuple[str, ...]]]) -> str:
    branches = []
    for command, (_, _, fields) in specs.items():
        values = ",".join(f"'{field}',data->'{field}'" for field in fields)
        expression = f"jsonb_build_object({values})"
        if "email" not in fields:
            expression = f"jsonb_strip_nulls({expression})"
        if fields == corrections_address:
            expression = f"jsonb_build_object('address',{expression})"
        branches.append(f"WHEN '{command}' THEN RETURN {expression};")
    return (
        "CREATE OR REPLACE FUNCTION canonical_correction_section(command text,data jsonb) "
        "RETURNS jsonb LANGUAGE plpgsql IMMUTABLE SET search_path=pg_catalog,public,pg_temp AS $$ "
        "BEGIN CASE command "
        + "\n".join(branches)
        + " ELSE RAISE EXCEPTION 'invalid correction command' USING ERRCODE='23514'; END CASE; END $$;"
    )


corrections_address = ("line1", "line2", "locality", "region", "postal_code", "country")


def upgrade() -> None:
    execute("LOCK TABLE worker_contacts,employer_contact_details IN SHARE ROW EXCLUSIVE MODE")
    op.add_column("worker_contacts", sa.Column("email", sa.String(320), nullable=True))
    op.add_column("employer_contact_details", sa.Column("email", sa.String(320), nullable=True))
    for table, constraint in (
        ("worker_contacts", "ck_worker_contacts_email_shape"),
        ("employer_contact_details", "ck_employer_contact_details_email_shape"),
    ):
        op.create_check_constraint(
            constraint,
            table,
            "email IS NULL OR (email=lower(email) AND char_length(email) BETWEEN 3 AND 320 "
            "AND email ~ '^[^@[:space:]]+@[^@[:space:]]+[.][^@[:space:]]+$')",
        )
    execute(
        "GRANT UPDATE(phone,email,version,updated_at,updated_by) ON worker_contacts TO golden_rose_runtime"
    )
    execute(
        "GRANT UPDATE(representative_name,phone,email,version,updated_at,updated_by) "
        "ON employer_contact_details TO golden_rose_runtime"
    )

    worker = module("0008_intake_finalization")
    worker_output = replace_function(worker.OUTPUT_AUTHORITY).replace(
        "to_jsonb(NEW)->>'phone' IS DISTINCT FROM candidate->>'phone'",
        "(to_jsonb(NEW)->>'phone',to_jsonb(NEW)->>'email') IS DISTINCT FROM "
        "(candidate->>'phone',candidate->>'email')",
    )
    execute(worker_output)

    employer = module("0008a_employer_finalization")
    employer_output = replace_function(employer.OUTPUT_AUTHORITY).replace(
        "(actual->>'representative_name',actual->>'phone') IS DISTINCT FROM\n    (candidate->>'representative_name',candidate->>'phone')",
        "(actual->>'representative_name',actual->>'phone',actual->>'email') IS DISTINCT FROM\n    (candidate->>'representative_name',candidate->>'phone',candidate->>'email')",
    )
    execute(employer_output)

    linked = module("0008c_intake_link_authority")
    snapshot = (
        replace_function(linked.SNAPSHOT)
        .replace(
            "'phone',facts->'worker_contact'->'phone',\n     'interests'",
            "'phone',facts->'worker_contact'->'phone','email',facts->'worker_contact'->'email',\n     'interests'",
        )
        .replace(
            "'phone',facts->'employer_contact_details'->'phone');",
            "'phone',facts->'employer_contact_details'->'phone','email',facts->'employer_contact_details'->'email');",
        )
    )
    execute(snapshot)

    corrections = module("0009_canonical_corrections")
    corrections.SPECS["correct_worker_contact"] = (
        "worker_contact",
        "worker_contacts",
        ("phone", "email"),
    )
    corrections.SPECS["correct_contact_details"] = (
        "employer_contact_details",
        "employer_contact_details",
        ("representative_name", "phone", "email"),
    )
    execute(correction_section_function(corrections.SPECS))
    guards = (
        replace_function(corrections.GUARDS)
        .replace(
            "WHEN 'worker_contact' THEN ARRAY['phone']",
            "WHEN 'worker_contact' THEN ARRAY['phone','email']",
        )
        .replace(
            "ARRAY['representative_name','phone','line1'",
            "ARRAY['representative_name','phone','email','line1'",
        )
    )
    execute(guards)

    reviews = module("0009a_canonical_reviews")
    current_facts = (
        replace_function(reviews.CURRENT_FACTS)
        .replace(
            "'full_name',records->'worker'->'full_name','phone',records->'worker_contact'->'phone',\n     'interests'",
            "'full_name',records->'worker'->'full_name','phone',records->'worker_contact'->'phone',\n     'email',records->'worker_contact'->'email','interests'",
        )
        .replace(
            "'representative_name',records->'employer_contact_details'->'representative_name','phone',records->'employer_contact_details'->'phone',\n     'role_title'",
            "'representative_name',records->'employer_contact_details'->'representative_name','phone',records->'employer_contact_details'->'phone',\n     'email',records->'employer_contact_details'->'email','role_title'",
        )
    )
    execute(current_facts)


def downgrade() -> None:
    execute("LOCK TABLE worker_contacts,employer_contact_details IN SHARE ROW EXCLUSIVE MODE")
    has_email = op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS(SELECT 1 FROM worker_contacts WHERE email IS NOT NULL) OR "
            "EXISTS(SELECT 1 FROM employer_contact_details WHERE email IS NOT NULL)"
        )
    )
    if has_email:
        raise RuntimeError("contact email data blocks downgrade before DDL")
    for table, constraint in (
        ("worker_contacts", "ck_worker_contacts_email_shape"),
        ("employer_contact_details", "ck_employer_contact_details_email_shape"),
    ):
        op.drop_constraint(constraint, table, type_="check")
    op.drop_column("employer_contact_details", "email")
    op.drop_column("worker_contacts", "email")
    worker = module("0008_intake_finalization")
    employer = module("0008a_employer_finalization")
    linked = module("0008c_intake_link_authority")
    corrections = module("0009_canonical_corrections")
    reviews = module("0009a_canonical_reviews")
    for sql in (
        worker.OUTPUT_AUTHORITY,
        employer.OUTPUT_AUTHORITY,
        linked.SNAPSHOT,
        corrections.section_function(),
        corrections.GUARDS,
        reviews.CURRENT_FACTS,
    ):
        execute(replace_function(sql))
    execute(
        "GRANT UPDATE(phone,version,updated_at,updated_by) ON worker_contacts TO golden_rose_runtime"
    )
    execute(
        "GRANT UPDATE(representative_name,phone,version,updated_at,updated_by) "
        "ON employer_contact_details TO golden_rose_runtime"
    )
