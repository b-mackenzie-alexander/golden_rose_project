"""Transaction-local reference writes governed by the additive link authority."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Column, DateTime, Integer, MetaData, Table, Uuid, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from golden_rose.application.intake_errors import IntakeError

PARTIES = ("worker", "employer")
CHILDREN = (
    "worker_contact",
    "worker_residence",
    "worker_preferences",
    "employer_contact",
    "employer_contact_details",
    "worksite",
    "employer_address",
)
# Separate mappings keep predecessor-migration fixtures from selecting future columns.
_metadata = MetaData()
_intakes = Table(
    "intakes",
    _metadata,
    Column("intake_id", Uuid, primary_key=True),
    Column("version", Integer),
    Column("content_version", Integer),
    Column("updated_at", DateTime(timezone=True)),
    Column("updated_by", Uuid),
    *(
        column
        for name in PARTIES
        for column in (
            Column(f"{name}_id", Uuid),
            Column(f"{name}_version", Integer),
        )
    ),
)
_links = Table(
    "intake_links",
    _metadata,
    Column("intake_id", Uuid, primary_key=True),
    *(Column(f"{name}_id", Uuid) for name in PARTIES),
    *(
        column
        for name in CHILDREN
        for column in (
            Column(f"{name}_id", Uuid),
            Column(f"{name}_version", Integer),
        )
    ),
)


def get_link_dependencies(session: Session, intake_id: UUID) -> dict[str, Any]:
    row = (
        session.execute(
            select(
                *(
                    _intakes.c[f"{name}_{suffix}"]
                    for name in PARTIES
                    for suffix in ("id", "version")
                ),
                *(
                    _links.c[f"{name}_{suffix}"]
                    for name in CHILDREN
                    for suffix in ("id", "version")
                ),
            )
            .select_from(_intakes.outerjoin(_links, _intakes.c.intake_id == _links.c.intake_id))
            .where(_intakes.c.intake_id == intake_id)
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise IntakeError("not_found", 404)
    result = {}
    for name in PARTIES + CHILDREN:
        identifier, version = row[f"{name}_id"], row[f"{name}_version"]
        if identifier is None and version is None:
            continue
        if identifier is None or version is None or version < 1:
            raise IntakeError("persistence_unavailable", 503)
        result[name] = {"id": str(identifier), "version": version}
    if result and len(set(result) & set(PARTIES)) != 1:
        raise IntakeError("persistence_unavailable", 503)
    return result


def write_link_dependencies(
    session: Session,
    *,
    intake_id: UUID,
    dependencies: dict[str, Any],
    version: int,
    content_version: int,
    updated_at: datetime,
    updated_by: UUID,
) -> None:
    """Replace references only; the caller owns locking, authority and commit.

    Unlink retains an empty child row. Parent-version refreshes need not rewrite
    identical children; the database still requires a real reference change.
    """
    parent: dict[str, Any] = {}
    children: dict[str, Any] = {}
    for name in PARTIES + CHILDREN:
        reference = dependencies.get(name)
        target = parent if name in PARTIES else children
        target[f"{name}_id"] = UUID(reference["id"]) if reference else None
        target[f"{name}_version"] = reference["version"] if reference else None
    session.execute(
        update(_intakes)
        .where(_intakes.c.intake_id == intake_id)
        .values(
            **parent,
            version=version,
            content_version=content_version,
            updated_at=updated_at,
            updated_by=updated_by,
        )
    )
    children.update({f"{name}_id": parent[f"{name}_id"] for name in PARTIES})
    if dependencies:
        session.execute(
            insert(_links)
            .values(intake_id=intake_id, **children)
            .on_conflict_do_update(
                index_elements=["intake_id"],
                set_=children,
                where=or_(
                    *(_links.c[key].is_distinct_from(value) for key, value in children.items())
                ),
            )
        )
    else:
        session.execute(update(_links).where(_links.c.intake_id == intake_id).values(**children))
