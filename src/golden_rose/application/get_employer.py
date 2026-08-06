from uuid import UUID

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from golden_rose.application.errors import EmployerNotFoundError
from golden_rose.auth.permissions import can_read_employer
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.employers import EmployerDetailRecord, get_employer_by_id


def get_employer(
    *,
    session: Session,
    principal: StaffPrincipal,
    employer_id: UUID,
) -> EmployerDetailRecord:
    if not can_read_employer(principal):
        msg = "principal lacks employer:read"
        raise PermissionError(msg)

    try:
        return get_employer_by_id(session=session, employer_id=employer_id)
    except NoResultFound as exc:
        raise EmployerNotFoundError("employer not found") from exc
