from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from golden_rose.api.errors import InvalidIdempotencyKeyError
from golden_rose.application.presentation_demo_seed import DEMO_INTAKE_PERMISSIONS
from golden_rose.application.staff_account_lifecycle import (
    StaffAccountNotFoundError,
    resolve_staff_principal_from_claims,
)
from golden_rose.auth.permissions import (
    CREATE_DRAFT_EMPLOYER_PERMISSION,
    EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
    EMPLOYER_CONTACT_READ_PERMISSION,
    EMPLOYER_DRAFT_REVISE_PERMISSION,
    EMPLOYER_READ_PERMISSION,
)
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.auth.staff_oidc import (
    StaffAccountUnavailableError,
    StaffAuthenticationFailedError,
    StaffAuthenticationRequiredError,
    StaffIdentityProviderUnavailableError,
    StaffOidcJwksTokenVerifier,
    StaffOidcTokenVerifier,
)
from golden_rose.config import Settings

staff_bearer = HTTPBearer(auto_error=False)


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


def get_staff_oidc_token_verifier() -> StaffOidcTokenVerifier:
    return StaffOidcJwksTokenVerifier()


def resolve_staff_principal_for_settings(
    settings: Settings,
    request: Request | None = None,
    credentials: HTTPAuthorizationCredentials | None = None,
    verifier: StaffOidcTokenVerifier | None = None,
) -> StaffPrincipal:
    if settings.auth_mode == "staff_oidc":
        if verifier is None:
            verifier = StaffOidcJwksTokenVerifier()
        return _get_staff_oidc_principal(
            settings=settings,
            request=request,
            credentials=credentials,
            verifier=verifier,
        )
    if settings.synthetic_staff_id is None:
        msg = "synthetic_staff_id is required for synthetic staff auth"
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


def get_staff_principal(
    settings: Annotated[Settings, Depends(get_settings)],
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(staff_bearer)],
    verifier: Annotated[StaffOidcTokenVerifier, Depends(get_staff_oidc_token_verifier)],
) -> StaffPrincipal:
    return resolve_staff_principal_for_settings(
        settings=settings,
        request=request,
        credentials=credentials,
        verifier=verifier,
    )


def _get_staff_oidc_principal(
    *,
    settings: Settings,
    request: Request | None,
    credentials: HTTPAuthorizationCredentials | None,
    verifier: StaffOidcTokenVerifier,
) -> StaffPrincipal:
    if request is None:
        raise StaffIdentityProviderUnavailableError("request context is required for staff auth")
    if credentials is None:
        raise StaffAuthenticationRequiredError("bearer staff authentication is required")
    try:
        claims = verifier.verify(token=credentials.credentials, settings=settings)
    except StaffIdentityProviderUnavailableError:
        raise
    except Exception as exc:
        raise StaffAuthenticationFailedError("staff identity token is invalid") from exc

    engine = getattr(request.app.state, "db_engine", None)
    if engine is None:
        raise StaffIdentityProviderUnavailableError("staff account store is not initialized")

    try:
        with Session(engine) as session:
            return resolve_staff_principal_from_claims(session=session, claims=claims)
    except StaffAccountNotFoundError as exc:
        raise StaffAuthenticationFailedError("staff account not found") from exc
    except PermissionError as exc:
        raise StaffAuthenticationFailedError("staff session does not satisfy policy") from exc
    except ValueError as exc:
        raise StaffAccountUnavailableError("staff account is unavailable") from exc


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
    principal = resolve_staff_principal_for_settings(settings)
    return StaffDirectory(
        (StaffDirectoryEntry(principal.actor_id, "Mariela Torres", True, principal.permissions),)
    )
