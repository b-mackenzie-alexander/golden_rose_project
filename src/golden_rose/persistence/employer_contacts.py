import hashlib
import json
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from golden_rose.persistence.models import employer_contacts


@dataclass(frozen=True, slots=True)
class EmployerContactRecord:
    employer_contact_id: UUID
    employer_id: UUID
    full_name: str
    created_at: object
    updated_at: object
    created_by: UUID
    updated_by: UUID
    version: int


def insert_employer_contact(
    *,
    session: Session,
    employer_contact_id: UUID,
    employer_id: UUID,
    full_name: str,
    created_by: UUID,
    created_at,
) -> EmployerContactRecord:
    session.execute(
        insert(employer_contacts).values(
            employer_contact_id=employer_contact_id,
            employer_id=employer_id,
            full_name=full_name,
            created_at=created_at,
            updated_at=created_at,
            created_by=created_by,
            updated_by=created_by,
            version=1,
        )
    )
    return EmployerContactRecord(
        employer_contact_id=employer_contact_id,
        employer_id=employer_id,
        full_name=full_name,
        created_at=created_at,
        updated_at=created_at,
        created_by=created_by,
        updated_by=created_by,
        version=1,
    )


def get_employer_contact_by_id(
    *, session: Session, employer_contact_id: UUID
) -> EmployerContactRecord:
    row = session.execute(
        select(
            employer_contacts.c.employer_contact_id,
            employer_contacts.c.employer_id,
            employer_contacts.c.full_name,
            employer_contacts.c.created_at,
            employer_contacts.c.updated_at,
            employer_contacts.c.created_by,
            employer_contacts.c.updated_by,
            employer_contacts.c.version,
        ).where(employer_contacts.c.employer_contact_id == employer_contact_id)
    ).one()
    return EmployerContactRecord(*row)


def build_create_employer_contact_request_fingerprint(
    *, employer_id: UUID, full_name: str
) -> bytes:
    payload = json.dumps(
        {
            "command_schema_version": 1,
            "command_type": "create_employer_contact",
            "employer_id": str(employer_id),
            "full_name": full_name,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).digest()
