"""Bounded canonical discovery with literal matching and authority-bound keysets."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.api.staff.worker_schemas import QueryWorkersRequest
from golden_rose.application.intake_cursors import binding, decode_cursor, encode_cursor
from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.models import workers


def query_workers(
    *,
    session: Session,
    principal: StaffPrincipal,
    request: QueryWorkersRequest,
) -> dict[str, Any]:
    if "worker:read" not in principal.permissions:
        raise IntakeError("forbidden", 403)
    bound = binding(
        principal,
        {
            "kind": "canonical_workers",
            "order": "created_at_desc_worker_id_desc",
            "query": request.model_dump(mode="json", exclude={"cursor"}),
            "worker_scope": None
            if principal.worker_scope is None
            else sorted(map(str, principal.worker_scope)),
        },
    )
    boundary = decode_cursor(request.cursor, bound)
    statement = select(
        workers.c.worker_id, workers.c.full_name, workers.c.version, workers.c.created_at
    )
    if principal.worker_scope is not None:
        statement = statement.where(workers.c.worker_id.in_(principal.worker_scope))
    if request.reference is not None:
        statement = statement.where(workers.c.worker_id == request.reference)
    else:
        escaped = (
            (request.name_query or "").replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        statement = statement.where(workers.c.full_name.ilike(f"%{escaped}%", escape="\\"))
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
                workers.c.created_at < instant,
                and_(workers.c.created_at == instant, workers.c.worker_id < identity),
            )
        )
    statement = statement.order_by(workers.c.created_at.desc(), workers.c.worker_id.desc()).limit(
        request.page_size + 1
    )
    try:
        rows = session.execute(statement).mappings().all()
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc
    selected = rows[: request.page_size]
    cursor = None
    if len(rows) > request.page_size:
        last = selected[-1]
        cursor = encode_cursor(
            bound, {"at": last["created_at"].isoformat(), "id": str(last["worker_id"])}
        )
    return {
        "items": [
            {key: row[key] for key in ("worker_id", "full_name", "version")} for row in selected
        ],
        "next_cursor": cursor,
    }
