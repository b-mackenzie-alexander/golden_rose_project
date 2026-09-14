"""Transaction-local command result writes; the caller owns commit/rollback."""

from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.orm import Session

from golden_rose.persistence.models import command_results


def insert_command_result(
    *,
    session: Session,
    command_id: UUID,
    entity_type: str,
    entity_id: UUID,
    result_version: int,
    event_type: str,
    actor_id: UUID,
    command_type: str,
) -> None:
    session.execute(
        insert(command_results).values(
            command_id=command_id,
            entity_type=entity_type,
            entity_id=entity_id,
            result_version=result_version,
            event_type=event_type,
            actor_id=actor_id,
            command_type=command_type,
        )
    )
