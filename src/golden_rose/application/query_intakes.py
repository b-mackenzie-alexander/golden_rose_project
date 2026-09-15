"""Shared, scoped keyset queries; cursors are signed and bound to authority."""

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Uuid, and_, case, column, exists, literal, or_, select, table
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_schemas import QueryIntakesRequest
from golden_rose.application.intake_commands import authorize_intake
from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.intakes import get_intake, intake_query_summary
from golden_rose.persistence.models import employers, intakes, workers

# Query only these successor columns; keep the shared predecessor mappings intact.
_LINK_REFERENCES = table(
    "intake_links",
    *(
        column(name, Uuid)
        for name in ("intake_id", "worker_id", "employer_id", "employer_contact_id", "worksite_id")
    ),
)

# Process-lifetime cursors deliberately expire on restart; records remain durable.
_CURSOR_KEY = secrets.token_bytes(32)


def _binding(principal: StaffPrincipal, query: QueryIntakesRequest) -> str:
    data = {
        "query": query.model_dump(mode="json", exclude={"cursor"}),
        "projection": 2,
        "worker_scope": None
        if principal.worker_scope is None
        else sorted(str(value) for value in principal.worker_scope),
        "actor": str(principal.actor_id),
        "permissions": sorted(principal.permissions),
        "scope": None
        if principal.intake_scope is None
        else sorted(str(value) for value in principal.intake_scope),
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def _encode(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.digest(_CURSOR_KEY, raw, "sha256")
    return base64.urlsafe_b64encode(signature + raw).decode().rstrip("=")


def _decode(cursor: str, binding: str) -> dict[str, Any]:
    try:
        raw = base64.b64decode(cursor + "=" * (-len(cursor) % 4), altchars=b"-_", validate=True)
        if not hmac.compare_digest(raw[:32], hmac.digest(_CURSOR_KEY, raw[32:], "sha256")):
            raise ValueError
        payload = json.loads(raw[32:])
        if set(payload) != {"v", "binding", "at", "id"} or payload["v"] != 1:
            raise ValueError
        if not hmac.compare_digest(payload["binding"], binding) or _encode(payload) != cursor:
            raise ValueError
        instant = datetime.fromisoformat(payload["at"])
        if instant.tzinfo is None:
            raise ValueError
        UUID(payload["id"])
        return dict(payload)
    except (ValueError, TypeError, KeyError, UnicodeError) as exc:
        raise IntakeError("invalid_cursor", 422) from exc


def _search_name(principal: StaffPrincipal, kind: str) -> Any:
    """Match only the same names that the caller may see in recovery summaries."""
    field = "full_name" if kind == "worker" else "display_name"
    candidate = intakes.c.content[field].astext
    parent_id = (
        select(_LINK_REFERENCES.c[f"{kind}_id"])
        .where(_LINK_REFERENCES.c.intake_id == intakes.c.intake_id)
        .correlate(intakes)
        .scalar_subquery()
    )
    required = {f"{kind}:read"}
    if kind == "worker":
        required.add("worker_contact:read")
    canonical: Any = literal(None)
    if required <= principal.permissions:
        table = workers if kind == "worker" else employers
        name_query = select(table.c[field]).where(table.c[f"{kind}_id"] == parent_id)
        if kind == "worker" and principal.worker_scope is not None:
            name_query = name_query.where(workers.c.worker_id.in_(principal.worker_scope))
        if kind == "employer":
            name_query = name_query.where(employers.c.lifecycle_status == "draft")
            for column, permissions in (
                ("employer_contact_id", {"employer_contact:read", "employer_contact:details:read"}),
                ("worksite_id", {"worksite:read"}),
            ):
                if not permissions <= principal.permissions:
                    selected_child = (
                        exists()
                        .where(
                            _LINK_REFERENCES.c.intake_id == intakes.c.intake_id,
                            _LINK_REFERENCES.c[column].is_not(None),
                        )
                        .correlate(intakes)
                    )
                    name_query = name_query.where(~selected_child)
        canonical = name_query.correlate(intakes).scalar_subquery()
    return case((parent_id.is_(None), candidate), else_=canonical)


def query_intakes(
    *, session: Session, principal: StaffPrincipal, request: QueryIntakesRequest
) -> dict[str, Any]:
    authorize_intake(principal, "intake:read")
    binding = _binding(principal, request)
    boundary = _decode(request.cursor, binding) if request.cursor else None
    statement = select(intakes.c.intake_id, intakes.c.created_at).where(
        intakes.c.kind == request.kind,
        intakes.c.lifecycle_status == request.lifecycle,
    )
    if principal.intake_scope is not None:
        statement = statement.where(intakes.c.intake_id.in_(principal.intake_scope))
    if request.reference:
        statement = statement.where(intakes.c.intake_id == request.reference)
    if request.name_query:
        escaped = request.name_query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        statement = statement.where(
            _search_name(principal, request.kind).ilike(
                f"%{escaped}%",
                escape="\\",
            )
        )
    if boundary:
        instant = datetime.fromisoformat(boundary["at"])
        statement = statement.where(
            or_(
                intakes.c.created_at < instant,
                and_(
                    intakes.c.created_at == instant,
                    intakes.c.intake_id < UUID(boundary["id"]),
                ),
            )
        )
    statement = statement.order_by(intakes.c.created_at.desc(), intakes.c.intake_id.desc()).limit(
        request.page_size + 1,
    )
    try:
        rows = session.execute(statement).all()
        selected = rows[: request.page_size]
        items = [
            intake_query_summary(session, get_intake(session, row.intake_id), principal)
            for row in selected
        ]
        cursor = None
        if len(rows) > request.page_size:
            last = selected[-1]
            cursor = _encode(
                {
                    "v": 1,
                    "binding": binding,
                    "at": last.created_at.isoformat(),
                    "id": str(last.intake_id),
                }
            )
        return {"items": items, "next_cursor": cursor}
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc
