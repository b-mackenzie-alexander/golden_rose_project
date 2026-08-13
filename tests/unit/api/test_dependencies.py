from types import SimpleNamespace
from typing import Annotated, cast
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from golden_rose.api.dependencies import get_db_session, get_staff_principal
from golden_rose.auth.permissions import (
    CREATE_DRAFT_EMPLOYER_PERMISSION,
    EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
    EMPLOYER_CONTACT_READ_PERMISSION,
    EMPLOYER_DRAFT_REVISE_PERMISSION,
    EMPLOYER_READ_PERMISSION,
)
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


def test_synthetic_principal_has_exact_create_and_read_permissions() -> None:
    staff_id = uuid4()
    settings = Settings(
        environment="local",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=staff_id,
    )

    principal = get_staff_principal(settings)

    assert principal.actor_id == staff_id
    assert principal.role_name == "synthetic_staff"
    assert principal.permissions == frozenset(
        {
            CREATE_DRAFT_EMPLOYER_PERMISSION,
            EMPLOYER_READ_PERMISSION,
            EMPLOYER_DRAFT_REVISE_PERMISSION,
            EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
            EMPLOYER_CONTACT_READ_PERMISSION,
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

    principal = get_staff_principal(settings)

    assert principal.actor_id == staff_id
    assert principal.role_name == "synthetic_staff"
    assert principal.permissions == frozenset(
        {
            CREATE_DRAFT_EMPLOYER_PERMISSION,
            EMPLOYER_READ_PERMISSION,
            EMPLOYER_DRAFT_REVISE_PERMISSION,
            EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
            EMPLOYER_CONTACT_READ_PERMISSION,
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

    principal = get_staff_principal(settings)

    assert principal.permissions == frozenset(
        {
            CREATE_DRAFT_EMPLOYER_PERMISSION,
            EMPLOYER_READ_PERMISSION,
            EMPLOYER_DRAFT_REVISE_PERMISSION,
            EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
            EMPLOYER_CONTACT_READ_PERMISSION,
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

    principal = get_staff_principal(settings)

    assert principal.actor_id == staff_id
    assert principal.role_name == "synthetic_staff"
    assert principal.permissions == frozenset(
        {
            CREATE_DRAFT_EMPLOYER_PERMISSION,
            EMPLOYER_READ_PERMISSION,
            EMPLOYER_DRAFT_REVISE_PERMISSION,
            EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
            EMPLOYER_CONTACT_READ_PERMISSION,
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

    principal = get_staff_principal(settings)

    assert principal.permissions == frozenset(
        {
            CREATE_DRAFT_EMPLOYER_PERMISSION,
            EMPLOYER_READ_PERMISSION,
            EMPLOYER_DRAFT_REVISE_PERMISSION,
            EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
            EMPLOYER_CONTACT_READ_PERMISSION,
        }
    )
    assert not hasattr(principal, "headers")
    assert not hasattr(principal, "request_headers")
