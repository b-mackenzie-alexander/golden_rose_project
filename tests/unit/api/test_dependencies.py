from types import SimpleNamespace
from typing import Annotated, cast
from uuid import UUID, uuid4

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

import golden_rose.api.dependencies as dependencies_module
from golden_rose.api.dependencies import (
    get_db_session,
    get_settings,
    get_staff_oidc_token_verifier,
    get_staff_principal,
    resolve_staff_principal_for_settings,
)
from golden_rose.api.errors import install_exception_handlers
from golden_rose.auth.permissions import (
    CREATE_DRAFT_EMPLOYER_PERMISSION,
    EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
    EMPLOYER_CONTACT_READ_PERMISSION,
    EMPLOYER_DRAFT_REVISE_PERMISSION,
    EMPLOYER_READ_PERMISSION,
)
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.auth.staff_accounts import StaffIdentityClaims
from golden_rose.auth.staff_oidc import StaffIdentityProviderUnavailableError
from golden_rose.config import Settings


class FakeSession:
    instances: list["FakeSession"] = []

    def __init__(self, engine) -> None:
        self.engine = engine
        self.closed = False
        FakeSession.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.closed = True


class FakeAuthSession:
    instances: list["FakeAuthSession"] = []

    def __init__(self, engine) -> None:
        self.engine = engine
        self.closed = False
        FakeAuthSession.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.closed = True


class FakeOidcVerifier:
    def __init__(self, claims: StaffIdentityClaims | Exception) -> None:
        self.claims = claims
        self.calls: list[tuple[str, Settings]] = []

    def verify(self, *, token: str, settings: Settings) -> StaffIdentityClaims:
        self.calls.append((token, settings))
        if isinstance(self.claims, Exception):
            raise self.claims
        return self.claims


def _staff_oidc_settings() -> Settings:
    return Settings(
        environment="test",
        auth_mode="staff_oidc",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=None,
        staff_oidc_issuer="https://accounts.example.test",
        staff_oidc_audience="golden-rose-staff",
        staff_oidc_jwks_url="https://accounts.example.test/.well-known/jwks.json",
    )


def _auth_probe_app(settings: Settings, verifier: FakeOidcVerifier | None = None) -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)
    app.state.db_engine = object()

    @app.get("/staff-auth-probe")
    def staff_auth_probe(
        principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    ) -> dict[str, object]:
        return {
            "actor_id": str(principal.actor_id),
            "role_name": principal.role_name,
            "permissions": sorted(principal.permissions),
        }

    app.dependency_overrides[get_settings] = lambda: settings
    if verifier is not None:
        app.dependency_overrides[get_staff_oidc_token_verifier] = lambda: verifier
    return app


def test_synthetic_principal_has_exact_create_and_read_permissions() -> None:
    staff_id = uuid4()
    settings = Settings(
        environment="local",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=staff_id,
    )

    principal = resolve_staff_principal_for_settings(settings)

    assert principal.actor_id == staff_id
    assert principal.role_name == "synthetic_staff"
    assert principal.permissions == frozenset(
        {
            CREATE_DRAFT_EMPLOYER_PERMISSION,
            EMPLOYER_READ_PERMISSION,
            EMPLOYER_DRAFT_REVISE_PERMISSION,
            EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
            EMPLOYER_CONTACT_READ_PERMISSION,
            "intake:review",
            "intake:follow_up",
            "intake:restricted_history:read",
            "work_interest:read",
            "work_interest:manage",
            "intake:read",
            "intake:draft:create",
            "intake:draft:revise",
            "worker_residence:read",
            "worker_residence:write",
            "party_address:read",
            "party_address:write",
            "worksite_address:read",
            "worksite_address:write",
        }
    )


def test_synthetic_principal_has_exact_bounded_employer_permissions() -> None:
    staff_id = uuid4()
    settings = Settings(
        environment="local",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=staff_id,
    )

    principal = resolve_staff_principal_for_settings(settings)

    assert principal.actor_id == staff_id
    assert principal.role_name == "synthetic_staff"
    assert principal.permissions == frozenset(
        {
            CREATE_DRAFT_EMPLOYER_PERMISSION,
            EMPLOYER_READ_PERMISSION,
            EMPLOYER_DRAFT_REVISE_PERMISSION,
            EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
            EMPLOYER_CONTACT_READ_PERMISSION,
            "intake:review",
            "intake:follow_up",
            "intake:restricted_history:read",
            "work_interest:read",
            "work_interest:manage",
            "intake:read",
            "intake:draft:create",
            "intake:draft:revise",
            "worker_residence:read",
            "worker_residence:write",
            "party_address:read",
            "party_address:write",
            "worksite_address:read",
            "worksite_address:write",
        }
    )


def test_request_headers_cannot_grant_read_permission() -> None:
    staff_id = uuid4()
    settings = Settings(
        environment="local",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=staff_id,
    )

    principal = resolve_staff_principal_for_settings(settings)

    assert principal.permissions == frozenset(
        {
            CREATE_DRAFT_EMPLOYER_PERMISSION,
            EMPLOYER_READ_PERMISSION,
            EMPLOYER_DRAFT_REVISE_PERMISSION,
            EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
            EMPLOYER_CONTACT_READ_PERMISSION,
            "intake:review",
            "intake:follow_up",
            "intake:restricted_history:read",
            "work_interest:read",
            "work_interest:manage",
            "intake:read",
            "intake:draft:create",
            "intake:draft:revise",
            "worker_residence:read",
            "worker_residence:write",
            "party_address:read",
            "party_address:write",
            "worksite_address:read",
            "worksite_address:write",
        }
    )
    assert not hasattr(principal, "headers")
    assert not hasattr(principal, "request_headers")


def test_get_db_session_reuses_application_owned_engine_and_closes_each_session(
    monkeypatch,
) -> None:
    from golden_rose.api import dependencies as dependencies_module

    FakeSession.instances.clear()
    monkeypatch.setattr(dependencies_module, "Session", FakeSession)

    shared_engine = object()
    request = cast(
        Request,
        SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db_engine=shared_engine))),
    )

    first_dependency = dependencies_module.get_db_session(request)
    second_dependency = dependencies_module.get_db_session(request)
    first_session = cast(FakeSession, next(first_dependency))
    second_session = cast(FakeSession, next(second_dependency))

    assert first_session.engine is shared_engine
    assert second_session.engine is shared_engine
    assert first_session is not second_session
    assert [session.engine for session in FakeSession.instances] == [shared_engine, shared_engine]
    assert FakeSession.instances[0].closed is False
    assert FakeSession.instances[1].closed is False

    with pytest.raises(StopIteration):
        next(first_dependency)
    with pytest.raises(StopIteration):
        next(second_dependency)

    assert FakeSession.instances[0].closed is True
    assert FakeSession.instances[1].closed is True


def test_get_db_session_requires_lifespan_owned_engine() -> None:
    from golden_rose.api import dependencies as dependencies_module

    request = cast(Request, SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace())))

    with pytest.raises(RuntimeError, match="application database engine is not initialized"):
        next(dependencies_module.get_db_session(request))


def test_get_db_session_supports_request_level_dependency_override() -> None:
    app = FastAPI()
    sentinel_session = object()
    override_finalized = False

    def override_db_session():
        nonlocal override_finalized
        try:
            yield sentinel_session
        finally:
            override_finalized = True

    @app.get("/session-probe")
    def session_probe(
        session: Annotated[object, Depends(get_db_session)],
    ) -> dict[str, bool]:
        return {"overridden": session is sentinel_session}

    app.dependency_overrides[get_db_session] = override_db_session

    with TestClient(app) as client:
        response = client.get("/session-probe")

    assert response.status_code == 200
    assert response.json() == {"overridden": True}
    assert override_finalized is True


def test_synthetic_principal_has_exact_bounded_employer_and_contact_permissions() -> None:
    staff_id = uuid4()
    settings = Settings(
        environment="local",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=staff_id,
    )

    principal = resolve_staff_principal_for_settings(settings)

    assert principal.actor_id == staff_id
    assert principal.role_name == "synthetic_staff"
    assert principal.permissions == frozenset(
        {
            CREATE_DRAFT_EMPLOYER_PERMISSION,
            EMPLOYER_READ_PERMISSION,
            EMPLOYER_DRAFT_REVISE_PERMISSION,
            EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
            EMPLOYER_CONTACT_READ_PERMISSION,
            "intake:review",
            "intake:follow_up",
            "intake:restricted_history:read",
            "work_interest:read",
            "work_interest:manage",
            "intake:read",
            "intake:draft:create",
            "intake:draft:revise",
            "worker_residence:read",
            "worker_residence:write",
            "party_address:read",
            "party_address:write",
            "worksite_address:read",
            "worksite_address:write",
        }
    )


def test_request_headers_cannot_grant_employer_contact_permissions() -> None:
    staff_id = uuid4()
    settings = Settings(
        environment="local",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=staff_id,
    )

    principal = resolve_staff_principal_for_settings(settings)

    assert principal.permissions == frozenset(
        {
            CREATE_DRAFT_EMPLOYER_PERMISSION,
            EMPLOYER_READ_PERMISSION,
            EMPLOYER_DRAFT_REVISE_PERMISSION,
            EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
            EMPLOYER_CONTACT_READ_PERMISSION,
            "intake:review",
            "intake:follow_up",
            "intake:restricted_history:read",
            "work_interest:read",
            "work_interest:manage",
            "intake:read",
            "intake:draft:create",
            "intake:draft:revise",
            "worker_residence:read",
            "worker_residence:write",
            "party_address:read",
            "party_address:write",
            "worksite_address:read",
            "worksite_address:write",
        }
    )
    assert not hasattr(principal, "headers")
    assert not hasattr(principal, "request_headers")


def test_staff_oidc_bearer_token_resolves_durable_staff_principal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    staff_id = UUID("22222222-2222-4222-8222-222222222222")
    settings = _staff_oidc_settings()
    verifier = FakeOidcVerifier(
        StaffIdentityClaims(
            provider_subject="oidc:staff:123",
            mfa_verified=True,
            session_id="session-123",
        )
    )
    observed: dict[str, object] = {}
    FakeAuthSession.instances.clear()

    def resolve_principal(*, session, claims):
        observed["session"] = session
        observed["claims"] = claims
        return StaffPrincipal(
            actor_id=staff_id,
            role_name="operations_staff",
            permissions=frozenset({"intake:read"}),
        )

    monkeypatch.setattr(dependencies_module, "Session", FakeAuthSession)
    monkeypatch.setattr(
        dependencies_module,
        "resolve_staff_principal_from_claims",
        resolve_principal,
    )
    app = _auth_probe_app(settings, verifier)

    with TestClient(app) as client:
        response = client.get(
            "/staff-auth-probe",
            headers={"Authorization": "Bearer signed-token"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "actor_id": str(staff_id),
        "role_name": "operations_staff",
        "permissions": ["intake:read"],
    }
    assert verifier.calls == [("signed-token", settings)]
    assert observed["claims"] == verifier.claims
    assert observed["session"] is FakeAuthSession.instances[0]
    assert FakeAuthSession.instances[0].closed is True


def test_staff_oidc_authentication_requires_bearer_token() -> None:
    settings = _staff_oidc_settings()
    verifier = FakeOidcVerifier(
        StaffIdentityClaims(provider_subject="oidc:staff:123", mfa_verified=True)
    )
    app = _auth_probe_app(settings, verifier)

    with TestClient(app) as client:
        response = client.get("/staff-auth-probe")

    assert response.status_code == 401
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["type"] == (
        "https://golden-rose.local/problems/staff-authentication-required"
    )
    assert verifier.calls == []


def test_staff_oidc_authentication_fails_closed_when_verifier_rejects_token() -> None:
    settings = _staff_oidc_settings()
    verifier = FakeOidcVerifier(ValueError("signature check failed"))
    app = _auth_probe_app(settings, verifier)

    with TestClient(app) as client:
        response = client.get(
            "/staff-auth-probe",
            headers={"Authorization": "Bearer bad-token"},
        )

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["detail"] == "staff authentication failed"


def test_staff_oidc_provider_unavailable_returns_no_store_service_unavailable() -> None:
    settings = _staff_oidc_settings()
    verifier = FakeOidcVerifier(StaffIdentityProviderUnavailableError("provider unavailable"))
    app = _auth_probe_app(settings, verifier)

    with TestClient(app) as client:
        response = client.get(
            "/staff-auth-probe",
            headers={"Authorization": "Bearer signed-token"},
        )

    assert response.status_code == 503
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["type"] == (
        "https://golden-rose.local/problems/staff-identity-provider-unavailable"
    )


def test_staff_oidc_missing_mfa_is_authentication_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _staff_oidc_settings()
    verifier = FakeOidcVerifier(
        StaffIdentityClaims(provider_subject="oidc:staff:123", mfa_verified=False)
    )

    def reject_missing_mfa(**_kwargs):
        raise PermissionError("staff session requires mfa")

    monkeypatch.setattr(dependencies_module, "Session", FakeAuthSession)
    monkeypatch.setattr(
        dependencies_module,
        "resolve_staff_principal_from_claims",
        reject_missing_mfa,
    )
    app = _auth_probe_app(settings, verifier)

    with TestClient(app) as client:
        response = client.get(
            "/staff-auth-probe",
            headers={"Authorization": "Bearer signed-token"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "staff authentication failed"


def test_staff_oidc_suspended_account_is_forbidden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _staff_oidc_settings()
    verifier = FakeOidcVerifier(
        StaffIdentityClaims(provider_subject="oidc:staff:123", mfa_verified=True)
    )

    def reject_suspended(**_kwargs):
        raise ValueError("staff account is not eligible for a session")

    monkeypatch.setattr(dependencies_module, "Session", FakeAuthSession)
    monkeypatch.setattr(
        dependencies_module,
        "resolve_staff_principal_from_claims",
        reject_suspended,
    )
    app = _auth_probe_app(settings, verifier)

    with TestClient(app) as client:
        response = client.get(
            "/staff-auth-probe",
            headers={"Authorization": "Bearer signed-token"},
        )

    assert response.status_code == 403
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["type"] == (
        "https://golden-rose.local/problems/staff-account-unavailable"
    )


def test_intake_permissions_are_available_in_private_synthetic_develop():
    settings = Settings(
        environment="local",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=uuid4(),
    ).model_copy(update={"environment": "develop"})
    principal = resolve_staff_principal_for_settings(settings)
    assert "intake:read" in principal.permissions
    assert "intake:draft:create" in principal.permissions
    assert "worker_residence:read" in principal.permissions
    assert principal.permissions > frozenset(
        {
            CREATE_DRAFT_EMPLOYER_PERMISSION,
            EMPLOYER_READ_PERMISSION,
            EMPLOYER_DRAFT_REVISE_PERMISSION,
            EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
            EMPLOYER_CONTACT_READ_PERMISSION,
        }
    )
