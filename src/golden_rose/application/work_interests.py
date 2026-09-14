"""Governed bilingual work-interest catalogs; no classification inference."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, insert, or_, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_review_schemas import (
    CreateWorkInterestRequest,
    QueryWorkInterestsRequest,
    ReviseWorkInterestRequest,
)
from golden_rose.application.intake_cursors import binding, decode_cursor, encode_cursor
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.intake_workflow_common import begin_command, write_authority
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.clock import Clock
from golden_rose.persistence.models import (
    entity_authorities,
    work_interest_versions,
    work_interests,
)


def authorize_catalog(principal: StaffPrincipal, manage: bool = False) -> None:
    required = {"work_interest:read"} | ({"work_interest:manage"} if manage else set())
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)


def interest_projection(row: Any) -> dict[str, Any]:
    return {
        key: str(row[key]) if key == "interest_id" else row[key]
        for key in ("interest_id", "code", "version", "label_en", "label_es", "active")
    }


def get_interest(session: Session, interest_id: UUID, *, lock: bool = False) -> dict[str, Any]:
    stmt = select(work_interests).where(work_interests.c.interest_id == interest_id)
    if lock:
        stmt = stmt.with_for_update()
    row = session.execute(stmt).mappings().one_or_none()
    if row is None:
        raise IntakeError("not_found", 404)
    return dict(row)


def execute_work_interest(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    request: CreateWorkInterestRequest | ReviseWorkInterestRequest,
    clock: Clock,
    interest_id: UUID | None = None,
) -> tuple[dict[str, Any], bool]:
    authorize_catalog(principal, True)
    creating = isinstance(request, CreateWorkInterestRequest)
    command_type = "create_work_interest" if creating else "revise_work_interest"
    try:
        fingerprint, receipt = begin_command(
            session,
            principal,
            command_id,
            command_type,
            interest_id,
            request.model_dump(mode="json", exclude_unset=True),
        )
        if receipt:
            row = get_interest(session, receipt["result_entity_id"])
            if row["version"] < receipt["result_record_version"]:
                raise IntakeError("persistence_unavailable", 503)
            result = {
                "command_id": str(command_id),
                "result_record_version": receipt["result_record_version"],
                "current": interest_projection(row),
            }
            session.rollback()
            return result, True
        now = clock.now()
        if isinstance(request, CreateWorkInterestRequest):
            interest_id, previous = uuid4(), 0
            row = {
                "interest_id": interest_id,
                "code": request.code,
                "version": 1,
                "label_en": request.label_en,
                "label_es": request.label_es,
                "active": True,
                "created_at": now,
                "created_by": principal.actor_id,
                "updated_at": now,
                "updated_by": principal.actor_id,
            }
            session.execute(insert(work_interests).values(**row))
            session.execute(
                insert(entity_authorities).values(
                    entity_type="work_interest", entity_id=interest_id, work_interest_id=interest_id
                )
            )
            changed = ["code", "label_en", "label_es", "active"]
        else:
            if interest_id is None:
                raise IntakeError("invalid_request", 422)
            row = get_interest(session, interest_id, lock=True)
            if row["version"] != request.expected_version:
                raise IntakeError("version_conflict")
            changes = {
                "label_en": request.label_en,
                "label_es": request.label_es,
                "active": request.active,
            }
            changed = sorted(key for key, value in changes.items() if row[key] != value)
            if not changed:
                raise IntakeError("no_change")
            previous = row["version"]
            row.update(
                **changes, version=previous + 1, updated_at=now, updated_by=principal.actor_id
            )
            session.execute(
                update(work_interests)
                .where(work_interests.c.interest_id == interest_id)
                .values(
                    **changes, version=row["version"], updated_at=now, updated_by=principal.actor_id
                )
            )
        event_type = "work_interest.created" if creating else "work_interest.revised"
        write_authority(
            session,
            principal=principal,
            command_id=command_id,
            command_type=command_type,
            fingerprint=fingerprint,
            entity_type="work_interest",
            entity_id=interest_id,
            previous_version=previous,
            event_type=event_type,
            event_id=uuid4(),
            now=now,
            changed=changed,
        )
        session.execute(
            insert(work_interest_versions).values(
                interest_id=interest_id,
                version=row["version"],
                label_en=row["label_en"],
                label_es=row["label_es"],
                active=row["active"],
                actor_id=principal.actor_id,
                occurred_at=now,
                command_id=command_id,
            )
        )
        result = {
            "command_id": str(command_id),
            "result_record_version": row["version"],
            "current": interest_projection(row),
        }
        session.commit()
        return result, False
    except IntegrityError as exc:
        session.rollback()
        if getattr(getattr(exc.orig, "diag", None), "constraint_name", None) in {
            "work_interests_code_key",
            "uq_work_interests_code",
        }:
            raise IntakeError("version_conflict") from exc
        raise IntakeError("persistence_unavailable", 503) from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc
    except Exception:
        session.rollback()
        raise


def query_work_interests(
    *, session: Session, principal: StaffPrincipal, request: QueryWorkInterestsRequest
) -> dict[str, Any]:
    authorize_catalog(principal)
    bound = binding(
        principal, {"route": "work-interests", **request.model_dump(exclude={"cursor"})}
    )
    position = decode_cursor(request.cursor, bound)
    stmt = select(work_interests)
    if not request.include_retired:
        stmt = stmt.where(work_interests.c.active.is_(True))
    if position:
        try:
            at, item_id = datetime.fromisoformat(position["at"]), UUID(position["id"])
            if at.utcoffset() is None:
                raise ValueError
        except (KeyError, TypeError, ValueError) as exc:
            raise IntakeError("invalid_cursor", 422) from exc
        stmt = stmt.where(
            or_(
                work_interests.c.created_at < at,
                and_(work_interests.c.created_at == at, work_interests.c.interest_id < item_id),
            )
        )
    rows = (
        session.execute(
            stmt.order_by(
                work_interests.c.created_at.desc(), work_interests.c.interest_id.desc()
            ).limit(request.page_size + 1)
        )
        .mappings()
        .all()
    )
    selected = rows[: request.page_size]
    cursor = (
        encode_cursor(
            bound,
            {"at": selected[-1]["created_at"].isoformat(), "id": str(selected[-1]["interest_id"])},
        )
        if len(rows) > request.page_size
        else None
    )
    return {"items": [interest_projection(row) for row in selected], "next_cursor": cursor}
