"""Populated upgrades preserve original evidence; irreversible history fails before DDL."""

import pytest
from sqlalchemy import text

from tests.integration.test_intake_link_authority import (
    AUTHORITY_TABLES,
    EMPLOYER_TABLES,
    WORKER_TABLES,
    api,
    canonical,
    rows,
)
from tests.integration.test_intake_migrations import migrate
from tests.integration.test_intake_migrations import migration_database as migration_database


def test_populated_prc_upgrade_and_unused_prd_downgrade_preserve_every_original_row(
    migration_database,
):
    migrate(migration_database, "0008c_intake_link_authority")
    with api(migration_database) as client:
        for kind in ("worker", "household", "business"):
            canonical(client, kind)
    tables = (
        *AUTHORITY_TABLES,
        *WORKER_TABLES,
        *EMPLOYER_TABLES,
        "intakes",
        "intake_addresses",
        "intake_reviews",
        "intake_review_payloads",
        "intake_finalizations",
    )
    before = {table: rows(migration_database, table) for table in tables}
    migrate(migration_database, "head")
    expected_after_upgrade = {
        table: [
            {
                **row,
                **(
                    {"email": None}
                    if table in {"worker_contacts", "employer_contact_details"}
                    else {}
                ),
            }
            for row in values
        ]
        for table, values in before.items()
    }
    assert {table: rows(migration_database, table) for table in tables} == expected_after_upgrade
    migrate(migration_database, "0008c_intake_link_authority", downgrade=True)
    assert {table: rows(migration_database, table) for table in tables} == before
    migrate(migration_database, "head")


def test_current_review_head_blocks_downgrade_before_schema_changes(migration_database):
    migrate(migration_database, "head")
    with api(migration_database) as client:
        canonical(client)
    with migration_database.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO canonical_review_heads(canonical_output_review_id,intake_id,version) "
                "SELECT intake_id,intake_id,0 FROM intake_finalizations"
            )
        )
    with pytest.raises(RuntimeError, match="before DDL"):
        migrate(migration_database, "0008c_intake_link_authority", downgrade=True)
    assert (
        rows(migration_database, "alembic_version")[0]["version_num"] == "0021_staff_google_binding"
    )
    assert len(rows(migration_database, "canonical_review_heads")) == 1
