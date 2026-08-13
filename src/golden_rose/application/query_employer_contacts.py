from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.application.contact_cursor import (
    ContactCursor,
    decode_contact_cursor,
    encode_contact_cursor,
)
from golden_rose.application.errors import EmployerNotFoundError, SafePersistenceError
from golden_rose.auth.permissions import can_read_employer
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.employer_contacts import EmployerContactRecord
from golden_rose.persistence.models import employer_contacts, employers


@dataclass(frozen=True, slots=True)
class EmployerContactPage:
    items: list[EmployerContactRecord]
    next_cursor: str | None


def query_employer_contacts(
    *,
    session: Session,
    principal: StaffPrincipal,
    employer_id: UUID,
    page_size: int,
    cursor: str | None,
) -> EmployerContactPage:
    if not can_read_employer(principal):
        msg = "principal lacks employer:read"
        raise PermissionError(msg)
    if "employer_contact:read" not in principal.permissions:
        msg = "principal lacks employer_contact:read"
        raise PermissionError(msg)

    after_created_at: datetime | None = None
    after_employer_contact_id: UUID | None = None
    if cursor is not None:
        decoded_cursor = decode_contact_cursor(
            cursor,
            expected_employer_id=employer_id,
            expected_page_size=page_size,
        )
        after_created_at = decoded_cursor.after_created_at
        after_employer_contact_id = decoded_cursor.after_employer_contact_id

    try:
        parent = session.execute(
            select(employers.c.employer_id).where(
                employers.c.employer_id == employer_id,
                employers.c.lifecycle_status == "draft",
            )
        ).one_or_none()
        if parent is None:
            raise EmployerNotFoundError("employer not found")

        statement = select(
            employer_contacts.c.employer_contact_id,
            employer_contacts.c.employer_id,
            employer_contacts.c.full_name,
            employer_contacts.c.created_at,
            employer_contacts.c.updated_at,
            employer_contacts.c.created_by,
            employer_contacts.c.updated_by,
            employer_contacts.c.version,
        ).where(employer_contacts.c.employer_id == employer_id)

        if after_created_at is not None and after_employer_contact_id is not None:
            statement = statement.where(
                or_(
                    employer_contacts.c.created_at < after_created_at,
                    and_(
                        employer_contacts.c.created_at == after_created_at,
                        employer_contacts.c.employer_contact_id < after_employer_contact_id,
                    ),
                )
            )

        statement = statement.order_by(
            employer_contacts.c.created_at.desc(),
            employer_contacts.c.employer_contact_id.desc(),
        ).limit(page_size + 1)

        rows = [EmployerContactRecord(*row) for row in session.execute(statement)]
        items = rows[:page_size]
        next_cursor = None
        if len(rows) > page_size and items:
            boundary = items[-1]
            boundary_created_at = session.execute(
                select(employer_contacts.c.created_at).where(
                    employer_contacts.c.employer_contact_id == boundary.employer_contact_id
                )
            ).scalar_one()
            next_cursor = encode_contact_cursor(
                ContactCursor(
                    version=1,
                    employer_id=employer_id,
                    page_size=page_size,
                    after_created_at=boundary_created_at,
                    after_employer_contact_id=boundary.employer_contact_id,
                )
            )
    except EmployerNotFoundError:
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc

    return EmployerContactPage(items=items, next_cursor=next_cursor)
