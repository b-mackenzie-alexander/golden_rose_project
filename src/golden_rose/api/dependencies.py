from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from golden_rose.api.errors import InvalidIdempotencyKeyError
from golden_rose.application.presentation_demo_seed import DEMO_INTAKE_PERMISSIONS
from golden_rose.auth.permissions import (
    CREATE_DRAFT_EMPLOYER_PERMISSION,
    EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
    EMPLOYER_CONTACT_READ_PERMISSION,
    EMPLOYER_DRAFT_REVISE_PERMISSION,
    EMPLOYER_READ_PERMISSION,
)
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.config import Settings


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class Uuid4IdentifierFactory:
    def new_uuid4(self) -> UUID:
        return uuid4()


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


def get_db_session(request: Request) -> Iterator[Session]:
    engine = getattr(request.app.state, "db_engine", None)
    if engine is None:
        msg = "application database engine is not initialized"
        raise RuntimeError(msg)
    with Session(engine) as session:
        yield session


def get_staff_principal(settings: Annotated[Settings, Depends(get_settings)]) -> StaffPrincipal:
    if settings.auth_mode != "synthetic" or settings.synthetic_staff_id is None:
        msg = "staff principal resolution requires a configured staff identity provider"
        raise RuntimeError(msg)
    intake_permissions = (
        DEMO_INTAKE_PERMISSIONS if settings.environment in {"local", "test", "develop"} else set()
    )
    return StaffPrincipal(
        actor_id=settings.synthetic_staff_id,
        role_name="synthetic_staff",
        permissions=frozenset(
            {
                CREATE_DRAFT_EMPLOYER_PERMISSION,
                EMPLOYER_READ_PERMISSION,
                EMPLOYER_DRAFT_REVISE_PERMISSION,
                EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
                EMPLOYER_CONTACT_READ_PERMISSION,
            }
            | intake_permissions
        ),
    )


def get_clock() -> SystemClock:
    return SystemClock()


def get_identifier_factory() -> Uuid4IdentifierFactory:
    return Uuid4IdentifierFactory()


def get_idempotency_key(
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> UUID:
    try:
        parsed = UUID(idempotency_key)
    except ValueError as exc:
        raise InvalidIdempotencyKeyError from exc

    if parsed.int == 0 or parsed.version != 4:
        raise InvalidIdempotencyKeyError

    return parsed


def get_staff_directory(settings: Annotated[Settings, Depends(get_settings)]):
    from golden_rose.auth.staff_directory import StaffDirectory, StaffDirectoryEntry

    if settings.environment not in {"local", "test"}:
        return StaffDirectory()
    principal = get_staff_principal(settings)
    return StaffDirectory(
        (StaffDirectoryEntry(principal.actor_id, "Mariela Torres", True, principal.permissions),)
    )
