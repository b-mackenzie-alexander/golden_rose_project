from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.application.errors import EmployerNotFoundError, SafePersistenceError
from golden_rose.auth.permissions import can_read_employer
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.employer_contacts import EmployerContactRecord
from golden_rose.persistence.models import employer_contacts, employers


def get_employer_contact(
    *,
    session: Session,
    principal: StaffPrincipal,
    employer_id: UUID,
    employer_contact_id: UUID,
) -> EmployerContactRecord:
    if not can_read_employer(principal):
        msg = "principal lacks employer:read"
        raise PermissionError(msg)
    if "employer_contact:read" not in principal.permissions:
        msg = "principal lacks employer_contact:read"
        raise PermissionError(msg)

    try:
        parent = session.execute(
            select(employers.c.employer_id).where(
                employers.c.employer_id == employer_id,
                employers.c.lifecycle_status == "draft",
            )
        ).one_or_none()
        if parent is None:
            raise EmployerNotFoundError("employer not found")

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
            ).where(
                employer_contacts.c.employer_id == employer_id,
                employer_contacts.c.employer_contact_id == employer_contact_id,
            )
        ).one()
    except EmployerNotFoundError:
        raise
    except NoResultFound as exc:
        raise EmployerNotFoundError("employer not found") from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc

    return EmployerContactRecord(*row)
