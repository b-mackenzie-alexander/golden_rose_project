"""Prepare concrete link storage; activation awaits atomic command integration."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008b_intake_link_storage"
down_revision = "0008a_employer_finalization"
branch_labels = None
depends_on = None

CHILDREN = {
    "worker_contact": ("worker", "worker_contacts"),
    "worker_residence": ("worker", "worker_residences"),
    "worker_preferences": ("worker", "worker_preferences"),
    "employer_contact": ("employer", "employer_contacts"),
    "employer_contact_details": ("employer", "employer_contact_details"),
    "worksite": ("employer", "worksites"),
    "employer_address": ("employer", "employer_addresses"),
}


def execute(sql: str) -> None:
    op.execute(sa.text(sql))


def reference(table: str, kind: str) -> None:
    op.add_column(table, sa.Column(f"{kind}_id", postgresql.UUID(as_uuid=True)))
    op.add_column(table, sa.Column(f"{kind}_version", sa.Integer()))
    op.create_check_constraint(
        f"ck_{table}_{kind}_reference",
        table,
        f"({kind}_id IS NULL AND {kind}_version IS NULL) OR "
        f"({kind}_id IS NOT NULL AND {kind}_version IS NOT NULL AND {kind}_version>=1)",
    )


def upgrade() -> None:
    execute("LOCK TABLE intakes,intake_links,employer_contact_details IN SHARE ROW EXCLUSIVE MODE")
    for kind, target in (("worker", "workers"), ("employer", "employers")):
        reference("intakes", kind)
        op.create_foreign_key(
            f"fk_intakes_{kind}", "intakes", target, [f"{kind}_id"], [f"{kind}_id"]
        )
        op.create_unique_constraint(
            f"uq_intakes_{kind}_link", "intakes", ["intake_id", f"{kind}_id"]
        )
        op.add_column("intake_links", sa.Column(f"{kind}_id", postgresql.UUID(as_uuid=True)))
        op.create_foreign_key(
            f"fk_intake_links_{kind}_parent",
            "intake_links",
            "intakes",
            ["intake_id", f"{kind}_id"],
            ["intake_id", f"{kind}_id"],
            deferrable=True,
            initially="DEFERRED",
        )
    op.create_check_constraint(
        "ck_intakes_link_kind",
        "intakes",
        "(kind='worker' AND employer_id IS NULL) OR (kind='employer' AND worker_id IS NULL)",
    )
    # Do not admit partial linking through old candidate-only review/finalization.
    op.create_check_constraint(
        "ck_intakes_links_not_available", "intakes", "worker_id IS NULL AND employer_id IS NULL"
    )
    op.create_unique_constraint(
        "uq_contact_details_link_parent",
        "employer_contact_details",
        ["employer_id", "employer_contact_id", "employer_contact_details_id"],
    )
    for name, (parent, target) in CHILDREN.items():
        reference("intake_links", name)
        if name == "employer_contact_details":
            local = ["employer_id", "employer_contact_id", "employer_contact_details_id"]
        else:
            local = [f"{parent}_id", f"{name}_id"]
        op.create_foreign_key(
            f"fk_intake_links_{name}",
            "intake_links",
            target,
            local,
            local,
            deferrable=True,
            initially="DEFERRED",
        )
    worker = ("worker_contact", "worker_residence", "worker_preferences")
    employer = ("employer_contact", "employer_contact_details", "worksite", "employer_address")
    op.create_check_constraint(
        "ck_intake_links_parent_shape",
        "intake_links",
        "(worker_id IS NOT NULL AND employer_id IS NULL AND "
        + " AND ".join(f"{name}_id IS NOT NULL" for name in worker)
        + " AND "
        + " AND ".join(f"{name}_id IS NULL" for name in employer)
        + ") OR (employer_id IS NOT NULL AND worker_id IS NULL AND "
        + " AND ".join(f"{name}_id IS NULL" for name in worker)
        + ")",
    )
    op.create_check_constraint(
        "ck_intake_links_contact_pair",
        "intake_links",
        "(employer_contact_id IS NULL AND employer_contact_details_id IS NULL) OR "
        "(employer_contact_id IS NOT NULL AND employer_contact_details_id IS NOT NULL)",
    )
    # Existing ck_intake_links_not_available and mutation/grant restrictions stay.


def downgrade() -> None:
    execute("LOCK TABLE intakes,intake_links,employer_contact_details IN SHARE ROW EXCLUSIVE MODE")
    intakes = sa.table("intakes", sa.column("worker_id"), sa.column("employer_id"))
    populated = sa.or_(
        sa.exists(sa.select(1).select_from(sa.table("intake_links"))),
        sa.exists(
            sa.select(1).where(
                sa.or_(intakes.c.worker_id.is_not(None), intakes.c.employer_id.is_not(None))
            )
        ),
    )
    if op.get_bind().execute(sa.select(populated)).scalar_one():
        raise RuntimeError("intake link data blocks downgrade before DDL")
    execute("SET CONSTRAINTS ALL IMMEDIATE")
    op.drop_constraint("ck_intake_links_contact_pair", "intake_links", type_="check")
    op.drop_constraint("ck_intake_links_parent_shape", "intake_links", type_="check")
    for name in reversed(CHILDREN):
        op.drop_constraint(f"fk_intake_links_{name}", "intake_links", type_="foreignkey")
        op.drop_constraint(f"ck_intake_links_{name}_reference", "intake_links", type_="check")
        op.drop_column("intake_links", f"{name}_version")
        op.drop_column("intake_links", f"{name}_id")
    op.drop_constraint("uq_contact_details_link_parent", "employer_contact_details", type_="unique")
    op.drop_constraint("ck_intakes_links_not_available", "intakes", type_="check")
    op.drop_constraint("ck_intakes_link_kind", "intakes", type_="check")
    for kind in ("employer", "worker"):
        op.drop_constraint(f"fk_intake_links_{kind}_parent", "intake_links", type_="foreignkey")
        op.drop_column("intake_links", f"{kind}_id")
        op.drop_constraint(f"uq_intakes_{kind}_link", "intakes", type_="unique")
        op.drop_constraint(f"fk_intakes_{kind}", "intakes", type_="foreignkey")
        op.drop_constraint(f"ck_intakes_{kind}_reference", "intakes", type_="check")
        op.drop_column("intakes", f"{kind}_version")
        op.drop_column("intakes", f"{kind}_id")
