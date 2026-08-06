from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.api.staff.schemas import SearchEmployersRequest
from golden_rose.application.errors import SafePersistenceError
from golden_rose.application.search_cursor import (
    CURSOR_TIMESTAMP_FORMAT,
    compute_filter_fingerprint,
    decode_search_cursor,
    encode_search_cursor,
)
from golden_rose.auth.permissions import can_read_employer
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.employers import EmployerSearchRecord
from golden_rose.persistence.models import employers


@dataclass(frozen=True, slots=True)
class SearchEmployersPage:
    items: list[EmployerSearchRecord]
    next_cursor: str | None


ESCAPE_CHARACTER = "\\"


def search_employers(
    *,
    session: Session,
    principal: StaffPrincipal,
    request: SearchEmployersRequest,
) -> SearchEmployersPage:
    if not can_read_employer(principal):
        msg = "principal lacks employer:read"
        raise PermissionError(msg)

    filter_fingerprint = compute_filter_fingerprint(
        display_name_query=request.display_name_query,
        employer_type=request.employer_type,
    )

    after_received_at: datetime | None = None
    after_employer_id: UUID | None = None
    if request.cursor is not None:
        cursor_payload = decode_search_cursor(
            request.cursor,
            expected_filter_fingerprint=filter_fingerprint,
        )
        after_received_at = datetime.strptime(
            str(cursor_payload["after_received_at"]),
            CURSOR_TIMESTAMP_FORMAT,
        ).replace(tzinfo=UTC)
        after_employer_id = UUID(str(cursor_payload["after_employer_id"]))

    statement = select(
        employers.c.employer_id,
        employers.c.employer_type,
        employers.c.display_name,
        employers.c.lifecycle_status,
        employers.c.received_at,
        employers.c.version,
    )

    statement = statement.where(
        employers.c.display_name.ilike(
            _contains_literal_pattern(request.display_name_query),
            escape=ESCAPE_CHARACTER,
        )
    )
    if request.employer_type is not None:
        statement = statement.where(employers.c.employer_type == request.employer_type)
    if after_received_at is not None and after_employer_id is not None:
        statement = statement.where(
            or_(
                employers.c.received_at < after_received_at,
                and_(
                    employers.c.received_at == after_received_at,
                    employers.c.employer_id < after_employer_id,
                ),
            )
        )

    statement = statement.order_by(
        employers.c.received_at.desc(),
        employers.c.employer_id.desc(),
    ).limit(request.page_size + 1)

    try:
        rows = [EmployerSearchRecord(*row) for row in session.execute(statement)]
    except SQLAlchemyError as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc
    items = rows[: request.page_size]

    next_cursor = None
    if len(rows) > request.page_size and items:
        boundary = items[-1]
        next_cursor = encode_search_cursor(
            after_received_at=boundary.received_at,
            after_employer_id=boundary.employer_id,
            filter_fingerprint=filter_fingerprint,
        )

    return SearchEmployersPage(items=items, next_cursor=next_cursor)


def _contains_literal_pattern(value: str) -> str:
    escaped = (
        value.replace(ESCAPE_CHARACTER, ESCAPE_CHARACTER * 2)
        .replace("%", ESCAPE_CHARACTER + "%")
        .replace("_", ESCAPE_CHARACTER + "_")
    )
    return f"%{escaped}%"
