from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from golden_rose.api.dependencies import (
    get_clock,
    get_identifier_factory,
    get_staff_principal,
)
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.main import create_app


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


class FixedIdentifierFactory:
    def __init__(self, *identifiers: UUID) -> None:
        self._identifiers = list(identifiers)

    def new_uuid4(self) -> UUID:
        return self._identifiers.pop(0)


def test_post_staff_employers_returns_201_and_exact_body_for_permitted_request(
    clean_tables,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("11111111-1111-4111-8111-111111111111")
    audit_event_id = UUID("44444444-4444-4444-8444-444444444444")
    fixed_now = datetime(2026, 8, 5, 0, 10, 45, tzinfo=UTC)

    app = create_app()
    app.dependency_overrides[get_clock] = lambda: FixedClock(fixed_now)
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        employer_id, audit_event_id
    )
    client = TestClient(app)

    response = client.post(
        "/api/staff/v1/employers",
        headers={"Idempotency-Key": "33333333-3333-4333-8333-333333333333"},
        json={
            "employer_type": "household",
            "display_name": "Synthetic Household API 001",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "employer_id": str(employer_id),
        "employer_type": "household",
        "display_name": "Synthetic Household API 001",
        "lifecycle_status": "draft",
        "source_channel": "staff_entry",
        "version": 1,
        "received_at": "2026-08-05T00:10:45Z",
        "created_at": "2026-08-05T00:10:45Z",
    }
    assert "location" not in {key.lower() for key in response.headers}


def test_post_staff_employers_identical_replay_returns_same_resource_with_replay_header(
    clean_tables,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("55555555-5555-4555-8555-555555555555")
    audit_event_id = UUID("66666666-6666-4666-8666-666666666666")
    app = create_app()
    app.dependency_overrides[get_clock] = lambda: FixedClock(
        datetime(2026, 8, 5, 0, 12, 0, tzinfo=UTC)
    )
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        employer_id,
        audit_event_id,
    )
    client = TestClient(app)

    first_response = client.post(
        "/api/staff/v1/employers",
        headers={"Idempotency-Key": "77777777-7777-4777-8777-777777777777"},
        json={
            "employer_type": "business",
            "display_name": "Synthetic Replay API 001",
        },
    )
    second_response = client.post(
        "/api/staff/v1/employers",
        headers={"Idempotency-Key": "77777777-7777-4777-8777-777777777777"},
        json={
            "employer_type": "business",
            "display_name": "Synthetic Replay API 001",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert second_response.json() == first_response.json()
    assert second_response.headers["Idempotency-Replayed"] == "true"


def test_post_staff_employers_conflicting_replay_returns_safe_409_problem_details(
    clean_tables,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    app = create_app()
    client = TestClient(app)

    first_response = client.post(
        "/api/staff/v1/employers",
        headers={"Idempotency-Key": "88888888-8888-4888-8888-888888888888"},
        json={
            "employer_type": "household",
            "display_name": "Synthetic Conflict API 001",
        },
    )
    conflict_response = client.post(
        "/api/staff/v1/employers",
        headers={"Idempotency-Key": "88888888-8888-4888-8888-888888888888"},
        json={
            "employer_type": "business",
            "display_name": "Synthetic Conflict API 001",
        },
    )

    assert first_response.status_code == 201
    assert conflict_response.status_code == 409
    assert conflict_response.json() == {
        "type": "https://golden-rose.local/problems/idempotency-conflict",
        "title": "Conflict",
        "detail": "idempotency conflict",
        "status": 409,
    }


def test_post_staff_employers_denied_principal_returns_403_without_writes(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    app = create_app()
    app.dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
        actor_id=UUID("99999999-9999-4999-8999-999999999999"),
        role_name="synthetic_staff",
        permissions=frozenset(),
    )
    client = TestClient(app)

    response = client.post(
        "/api/staff/v1/employers",
        headers={"Idempotency-Key": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"},
        json={
            "employer_type": "household",
            "display_name": "Synthetic Denied API 001",
        },
    )

    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert response.status_code == 403
    assert response.json() == {
        "type": "https://golden-rose.local/problems/forbidden",
        "title": "Forbidden",
        "detail": "forbidden",
        "status": 403,
    }
    assert employer_count == 0
    assert command_receipt_count == 0
    assert audit_event_count == 0


@pytest.mark.parametrize(
    ("headers", "label"),
    [
        ({}, "missing"),
        ({"Idempotency-Key": "not-a-uuid"}, "malformed"),
        ({"Idempotency-Key": "00000000-0000-0000-0000-000000000000"}, "nil"),
        ({"Idempotency-Key": "11111111-1111-1111-8111-111111111111"}, "non-v4"),
    ],
)
def test_post_staff_employers_invalid_idempotency_key_returns_safe_400(
    clean_tables,
    monkeypatch,
    headers,
    label,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    client = TestClient(create_app())

    response = client.post(
        "/api/staff/v1/employers",
        headers=headers,
        json={
            "employer_type": "household",
            "display_name": f"Synthetic Invalid Idempotency {label}",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "type": "https://golden-rose.local/problems/invalid-idempotency-key",
        "title": "Bad Request",
        "detail": "invalid idempotency key",
        "status": 400,
    }


def test_post_staff_employers_body_violations_return_safe_422(
    clean_tables,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    client = TestClient(create_app())

    response = client.post(
        "/api/staff/v1/employers",
        headers={"Idempotency-Key": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"},
        json={
            "employer_type": "invalid",
            "display_name": "\t",
            "created_by": "malicious",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "type": "https://golden-rose.local/problems/request-validation",
        "title": "Unprocessable Entity",
        "detail": "request validation failed",
        "status": 422,
    }


def test_post_staff_employers_actor_role_permission_headers_cannot_elevate_authority(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    app = create_app()
    app.dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
        actor_id=UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
        role_name="synthetic_staff",
        permissions=frozenset(),
    )
    client = TestClient(app)

    response = client.post(
        "/api/staff/v1/employers",
        headers={
            "Idempotency-Key": "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
            "X-Actor-Id": "11111111-1111-4111-8111-111111111111",
            "X-Role-Name": "platform_administrator",
            "X-Permissions": "employer:draft:create",
        },
        json={
            "employer_type": "household",
            "display_name": "Synthetic Header Escalation 001",
        },
    )

    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert response.status_code == 403
    assert employer_count == 0
    assert command_receipt_count == 0
    assert audit_event_count == 0


def test_post_staff_employers_known_database_unavailability_returns_safe_503(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    import golden_rose.api.staff.employers as employers_module
    from golden_rose.application.errors import SafePersistenceError

    def raise_safe_persistence_error(**_: object):
        raise SafePersistenceError("persistence operation failed")

    monkeypatch.setattr(
        employers_module,
        "create_draft_employer",
        raise_safe_persistence_error,
    )
    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.post(
        "/api/staff/v1/employers",
        headers={"Idempotency-Key": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"},
        json={
            "employer_type": "household",
            "display_name": "Synthetic Service Unavailable 001",
        },
    )

    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert response.status_code == 503
    assert response.json() == {
        "type": "https://golden-rose.local/problems/service-unavailable",
        "title": "Service Unavailable",
        "detail": "service unavailable",
        "status": 503,
    }
    assert employer_count == 0
    assert command_receipt_count == 0
    assert audit_event_count == 0


def test_post_staff_employers_unexpected_failure_returns_safe_500(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    import golden_rose.api.staff.employers as employers_module

    def raise_unexpected_error(**_: object):
        raise RuntimeError("boom with secret-like text")

    monkeypatch.setattr(
        employers_module,
        "create_draft_employer",
        raise_unexpected_error,
    )
    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.post(
        "/api/staff/v1/employers",
        headers={"Idempotency-Key": "ffffffff-ffff-4fff-8fff-ffffffffffff"},
        json={
            "employer_type": "household",
            "display_name": "Synthetic Internal Error 001",
        },
    )

    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert response.status_code == 500
    assert response.json() == {
        "type": "https://golden-rose.local/problems/internal-error",
        "title": "Internal Server Error",
        "detail": "internal server error",
        "status": 500,
    }
    assert employer_count == 0
    assert command_receipt_count == 0
    assert audit_event_count == 0


def test_openapi_exposes_only_intended_staff_route() -> None:
    client = TestClient(create_app())

    openapi = client.get("/openapi.json")

    assert openapi.status_code == 200
    paths = openapi.json()["paths"]
    assert set(paths) == {
        "/api/staff/v1/employers",
        "/api/staff/v1/employers/search",
        "/api/staff/v1/employers/{employer_id}",
    }
    assert set(paths["/api/staff/v1/employers"]) == {"post"}
    assert set(paths["/api/staff/v1/employers/search"]) == {"post"}
    assert set(paths["/api/staff/v1/employers/{employer_id}"]) == {"get"}
