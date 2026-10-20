"""Transaction-local insertion of complete canonical worker records."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import insert
from sqlalchemy.orm import Session

from golden_rose.application.intake_contracts import Address, WorkerDraftContent
from golden_rose.persistence.models import (
    entity_authorities,
    worker_contacts,
    worker_interest_selections,
    worker_preferences,
    worker_residences,
    workers,
)


def insert_worker_group(
    session: Session,
    *,
    content: dict[str, Any],
    address: dict[str, str],
    actor_id: UUID,
    now: datetime,
) -> dict[str, UUID]:
    """The finalizer owns completeness, permissions, review, events and commit."""
    content = WorkerDraftContent.model_validate(content).to_content()
    address = Address.model_validate(address).to_content()
    identities = {
        kind: uuid4()
        for kind in ("worker", "worker_contact", "worker_residence", "worker_preferences")
    }
    attribution = {
        "version": 1,
        "created_at": now,
        "updated_at": now,
        "created_by": actor_id,
        "updated_by": actor_id,
    }
    for kind, table, values in (
        ("worker", workers, {"full_name": content["full_name"]}),
        (
            "worker_contact",
            worker_contacts,
            {
                "phone": content["phone"],
                **({"email": content["email"]} if "email" in content else {}),
            },
        ),
        ("worker_residence", worker_residences, address),
        (
            "worker_preferences",
            worker_preferences,
            {
                "interests": content["interests"],
                "availability": content["availability"],
                "self_reported": True,
            },
        ),
    ):
        record: dict[str, Any] = {**values, **attribution, f"{kind}_id": identities[kind]}
        if kind != "worker":
            record["worker_id"] = identities["worker"]
        session.execute(insert(table).values(**record))
        session.execute(
            insert(entity_authorities).values(
                entity_type=kind, entity_id=identities[kind], **{f"{kind}_id": identities[kind]}
            )
        )
    for selection in content["interests"].get("selections", []):
        session.execute(
            insert(worker_interest_selections).values(
                worker_preferences_id=identities["worker_preferences"],
                interest_id=UUID(selection["interest_id"]),
                catalog_version=selection["catalog_version"],
            )
        )
    return identities
