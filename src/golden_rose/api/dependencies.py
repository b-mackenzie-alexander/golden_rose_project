from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from golden_rose.api.errors import InvalidIdempotencyKeyError
from golden_rose.auth.permissions import (
    CREATE_DRAFT_EMPLOYER_PERMISSION,
    EMPLOYER_READ_PERMISSION,
)
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.config import Settings
from golden_rose.database import create_database_engine


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class Uuid4IdentifierFactory:
    def new_uuid4(self) -> UUID:
        return uuid4()


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


def get_db_session() -> Iterator[Session]:
    engine = create_database_engine()
    with Session(engine) as session:
        yield session


def get_staff_principal(settings: Annotated[Settings, Depends(get_settings)]) -> StaffPrincipal:
    return StaffPrincipal(
        actor_id=settings.synthetic_staff_id,
        role_name="synthetic_staff",
        permissions=frozenset({CREATE_DRAFT_EMPLOYER_PERMISSION, EMPLOYER_READ_PERMISSION}),
    )


def get_clock() -> SystemClock:
    return SystemClock()


def get_identifier_factory() -> Uuid4IdentifierFactory:
    return Uuid4IdentifierFactory()


def get_idempotency_key(
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> UUID:
    if idempotency_key is None:
        raise InvalidIdempotencyKeyError

    try:
        parsed = UUID(idempotency_key)
    except ValueError as exc:
        raise InvalidIdempotencyKeyError from exc

    if parsed.int == 0 or parsed.version != 4:
        raise InvalidIdempotencyKeyError

    return parsed
