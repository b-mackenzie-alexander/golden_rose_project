from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.orm import Session

from golden_rose.persistence.models import entity_authorities


def insert_employer_authority(*, session: Session, employer_id: UUID) -> None:
    session.execute(
        insert(entity_authorities).values(
            entity_type="employer",
            entity_id=employer_id,
            employer_id=employer_id,
            employer_contact_id=None,
        )
    )


def insert_employer_contact_authority(*, session: Session, employer_contact_id: UUID) -> None:
    session.execute(
        insert(entity_authorities).values(
            entity_type="employer_contact",
            entity_id=employer_contact_id,
            employer_id=None,
            employer_contact_id=employer_contact_id,
        )
    )
