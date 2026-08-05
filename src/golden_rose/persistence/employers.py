from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from golden_rose.persistence.models import employers


@dataclass(frozen=True, slots=True)
class EmployerRecord:
    employer_id: UUID
    employer_type: Literal["household", "business"]
    display_name: str
    lifecycle_status: Literal["draft"]
    source_channel: Literal["staff_entry"]
    received_at: datetime
    created_at: datetime
    created_by: UUID
    version: int


def insert_draft_employer(
    *,
    session: Session,
    employer_id: UUID,
    employer_type: Literal["household", "business"],
    display_name: str,
    created_by: UUID,
    created_at: datetime,
) -> EmployerRecord:
    session.execute(
        insert(employers).values(
            employer_id=employer_id,
            employer_type=employer_type,
            display_name=display_name,
            lifecycle_status="draft",
            source_channel="staff_entry",
            received_at=created_at,
            created_at=created_at,
            created_by=created_by,
            version=1,
        )
    )
    return EmployerRecord(
        employer_id=employer_id,
        employer_type=employer_type,
        display_name=display_name,
        lifecycle_status="draft",
        source_channel="staff_entry",
        received_at=created_at,
        created_at=created_at,
        created_by=created_by,
        version=1,
    )


def get_employer_by_id(*, session: Session, employer_id: UUID) -> EmployerRecord:
    row = session.execute(
        select(
            employers.c.employer_id,
            employers.c.employer_type,
            employers.c.display_name,
            employers.c.lifecycle_status,
            employers.c.source_channel,
            employers.c.received_at,
            employers.c.created_at,
            employers.c.created_by,
            employers.c.version,
        ).where(employers.c.employer_id == employer_id)
    ).one()
    return EmployerRecord(*row)
