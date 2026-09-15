"""Minimized parent queries using authority-bound descending canonical keysets."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from golden_rose.api.staff.employer_output_schemas import QueryEmployerOutputsRequest
from golden_rose.application.intake_cursors import binding, decode_cursor, encode_cursor
from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.models import (
    employer_addresses,
    employers,
    staffing_requests,
    worksites,
)

EmployerOutputKind = Literal["addresses", "worksites", "requests"]


def query_employer_outputs(
    *,
    session: Session,
    principal: StaffPrincipal,
    employer_id: UUID,
    kind: EmployerOutputKind,
    request: QueryEmployerOutputsRequest,
) -> dict[str, Any]:
    permission = {
        "addresses": "party_address:read",
        "worksites": "worksite:read",
        "requests": "staffing_request:read",
    }[kind]
    if not {"employer:read", permission} <= principal.permissions:
        raise IntakeError("forbidden", 403)
    bound = binding(
        principal,
        {
            "kind": f"canonical_employer_{kind}",
            "parent": str(employer_id),
            "order": "created_at_desc_id_desc",
            "scope": "shared_synthetic_employers",
            "query": request.model_dump(mode="json", exclude={"cursor"}),
        },
    )
    boundary = decode_cursor(request.cursor, bound)
    table, id_name, names = {
        "addresses": (employer_addresses, "employer_address_id", ("purpose",)),
        "worksites": (worksites, "worksite_id", ()),
        "requests": (
            staffing_requests,
            "staffing_request_id",
            ("request_status", "role_title", "worker_count"),
        ),
    }[kind]
    columns: list[ColumnElement[Any]] = [
        table.c[id_name],
        table.c.employer_id,
        table.c.version,
        table.c.created_at,
        *(table.c[name] for name in names),
    ]
    if kind == "requests":
        # Remove free-text terms in SQL, before the summary crosses the read boundary.
        columns.append(table.c.offer.op("-")("terms").label("offer"))
    statement = select(*columns).where(table.c.employer_id == employer_id)
    if boundary is not None:
        try:
            if set(boundary) != {"at", "id"}:
                raise ValueError
            instant = datetime.fromisoformat(boundary["at"])
            identity = UUID(boundary["id"])
            if instant.tzinfo is None:
                raise ValueError
        except (ValueError, TypeError, AttributeError) as exc:
            raise IntakeError("invalid_cursor", 422) from exc
        statement = statement.where(
            or_(
                table.c.created_at < instant,
                and_(table.c.created_at == instant, table.c[id_name] < identity),
            )
        )
    statement = statement.order_by(table.c.created_at.desc(), table.c[id_name].desc()).limit(
        request.page_size + 1
    )
    try:
        parent = session.execute(
            select(employers.c.employer_id).where(
                employers.c.employer_id == employer_id, employers.c.lifecycle_status == "draft"
            )
        ).one_or_none()
        if parent is None:
            raise IntakeError("not_found", 404)
        rows = session.execute(statement).mappings().all()
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc
    selected = rows[: request.page_size]
    cursor = None
    if len(rows) > request.page_size:
        last = selected[-1]
        cursor = encode_cursor(
            bound, {"at": last["created_at"].isoformat(), "id": str(last[id_name])}
        )
    fields = (
        id_name,
        "employer_id",
        "version",
        *names,
        *(("offer",) if kind == "requests" else ()),
    )
    return {
        "items": [{name: row[name] for name in fields} for row in selected],
        "next_cursor": cursor,
    }
