from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

import golden_rose.api.staff.employers as employers_module
from golden_rose.api.dependencies import (
    get_clock,
    get_identifier_factory,
    get_staff_principal,
)
from golden_rose.application.errors import SafePersistenceError
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
    with TestClient(app) as client:
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
        assert response.headers["Cache-Control"] == "no-store"
        assert "location" not in {key.lower() for key in response.headers}


def test_post_staff_employers_fresh_and_replay_emit_result_version_without_changing_create_status_or_body_contract(  # noqa: E501
    clean_tables,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("66666666-aaaa-4aaa-8aaa-666666666666")
    audit_event_id = UUID("67676767-bbbb-4bbb-8bbb-676767676767")
    app = create_app()
    app.dependency_overrides[get_clock] = lambda: FixedClock(
        datetime(2026, 8, 11, 2, 25, 0, tzinfo=UTC)
    )
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        employer_id, audit_event_id
    )
    with TestClient(app) as client:
        first_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "68686868-cccc-4ccc-8ccc-686868686868"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Create Result Version",
            },
        )
        replay_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "68686868-cccc-4ccc-8ccc-686868686868"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Create Result Version",
            },
        )

        expected_body = {
            "employer_id": str(employer_id),
            "employer_type": "household",
            "display_name": "Synthetic Create Result Version",
            "lifecycle_status": "draft",
            "source_channel": "staff_entry",
            "version": 1,
            "received_at": "2026-08-11T02:25:00Z",
            "created_at": "2026-08-11T02:25:00Z",
        }

        assert first_response.status_code == 201
        assert replay_response.status_code == 201
        assert first_response.headers["Cache-Control"] == "no-store"
        assert replay_response.headers["Cache-Control"] == "no-store"
        assert first_response.headers["Idempotency-Result-Version"] == "1"
        assert replay_response.headers["Idempotency-Result-Version"] == "1"
        assert "Idempotency-Replayed" not in first_response.headers
        assert replay_response.headers["Idempotency-Replayed"] == "true"
        assert first_response.json() == expected_body
        assert replay_response.json() == expected_body


def test_post_staff_employers_replay_after_revision_returns_current_truth_and_original_result_version(  # noqa: E501
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("69696969-aaaa-4aaa-8aaa-696969696969")
    create_audit_event_id = UUID("70707070-bbbb-4bbb-8bbb-707070707070")
    revision_audit_event_id = UUID("71717171-cccc-4ccc-8ccc-717171717171")
    create_key = "72727272-dddd-4ddd-8ddd-727272727272"
    app = create_app()
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        employer_id, create_audit_event_id, revision_audit_event_id
    )
    with TestClient(app) as client:
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 11, 2, 30, 0, tzinfo=UTC)
        )
        create_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": create_key},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Create Replay Before Revision",
            },
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 11, 2, 35, 0, tzinfo=UTC)
        )
        revision_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": "73737373-eeee-4eee-8eee-737373737373"},
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Create Replay After Revision",
            },
        )
        receipt_count_before_replay = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count_before_replay = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()
        replay_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": create_key},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Create Replay Before Revision",
            },
        )

        receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
        audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

        assert create_response.status_code == 201
        assert create_response.headers["Idempotency-Result-Version"] == "1"
        assert revision_response.status_code == 200
        assert revision_response.headers["Idempotency-Result-Version"] == "2"
        assert replay_response.status_code == 201
        assert replay_response.headers["Cache-Control"] == "no-store"
        assert replay_response.headers["Idempotency-Result-Version"] == "1"
        assert replay_response.headers["Idempotency-Replayed"] == "true"
        assert replay_response.json() == {
            "employer_id": str(employer_id),
            "employer_type": "business",
            "display_name": "Synthetic Create Replay After Revision",
            "lifecycle_status": "draft",
            "source_channel": "staff_entry",
            "version": 2,
            "received_at": "2026-08-11T02:30:00Z",
            "created_at": "2026-08-11T02:30:00Z",
        }
        assert receipt_count_before_replay == 2
        assert audit_event_count_before_replay == 2
        assert receipt_count == receipt_count_before_replay
        assert audit_event_count == audit_event_count_before_replay


def test_post_staff_employer_revision_returns_exact_200_contract(
    clean_tables,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("12121212-aaaa-4aaa-8aaa-121212121212")
    audit_event_id = UUID("13131313-bbbb-4bbb-8bbb-131313131313")
    app = create_app()
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        employer_id, audit_event_id
    )
    app.dependency_overrides[get_clock] = lambda: FixedClock(
        datetime(2026, 8, 11, 1, 0, 0, tzinfo=UTC)
    )
    with TestClient(app) as client:
        create_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "14141414-cccc-4ccc-8ccc-141414141414"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Revision API Seed",
            },
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 11, 1, 5, 0, tzinfo=UTC)
        )
        response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": "15151515-dddd-4ddd-8ddd-151515151515"},
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Revision API Updated",
            },
        )

        assert create_response.status_code == 201
        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
        assert response.headers["Idempotency-Result-Version"] == "2"
        assert "Idempotency-Replayed" not in response.headers
        assert response.json() == {
            "employer_id": str(employer_id),
            "employer_type": "business",
            "display_name": "Synthetic Revision API Updated",
            "lifecycle_status": "draft",
            "source_channel": "staff_entry",
            "version": 2,
            "received_at": "2026-08-11T01:00:00Z",
            "created_at": "2026-08-11T01:00:00Z",
            "updated_at": "2026-08-11T01:05:00Z",
        }


@pytest.mark.parametrize(
    ("display_name", "message"),
    [
        ("   ", "display_name must not be blank"),
        ("x" * 201, "display_name must be 200 characters or fewer"),
        ("Bad\nName", "display_name must not contain control characters"),
    ],
)
def test_post_staff_employer_revision_rejects_invalid_display_name_without_writes(
    clean_tables,
    monkeypatch,
    session,
    display_name: str,
    message: str,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("20202020-aaaa-4aaa-8aaa-202020202020")
    audit_event_id = UUID("21212121-bbbb-4bbb-8bbb-212121212121")
    app = create_app()
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        employer_id, audit_event_id
    )
    app.dependency_overrides[get_clock] = lambda: FixedClock(
        datetime(2026, 8, 11, 1, 0, 0, tzinfo=UTC)
    )

    with TestClient(app) as client:
        create_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "22222222-cccc-4ccc-8ccc-222222222222"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Revision Validation Seed",
            },
        )

        receipt_count_before = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count_before = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()

        response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": "23232323-dddd-4ddd-8ddd-232323232323"},
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": display_name,
            },
        )

        employer = (
            session.execute(
                text(
                    """
                    SELECT employer_type, display_name, version
                    FROM employers
                    WHERE employer_id = :employer_id
                    """
                ),
                {"employer_id": employer_id},
            )
            .mappings()
            .one()
        )
        receipt_count_after = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count_after = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()

    assert create_response.status_code == 201
    assert response.status_code == 422
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json() == {
        "type": "https://golden-rose.local/problems/request-validation",
        "title": "Unprocessable Entity",
        "detail": "request validation failed",
        "status": 422,
    }
    assert dict(employer) == {
        "employer_type": "household",
        "display_name": "Synthetic Revision Validation Seed",
        "version": 1,
    }
    assert receipt_count_before == 1
    assert audit_event_count_before == 1
    assert receipt_count_after == 1
    assert audit_event_count_after == 1


def test_post_staff_employer_revision_replay_returns_current_truth_and_result_headers(
    clean_tables,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("16161616-aaaa-4aaa-8aaa-161616161616")
    audit_event_id = UUID("17171717-bbbb-4bbb-8bbb-171717171717")
    app = create_app()
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        employer_id, audit_event_id
    )
    with TestClient(app) as client:
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 11, 1, 10, 0, tzinfo=UTC)
        )
        create_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "18181818-cccc-4ccc-8ccc-181818181818"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Revision Replay API Seed",
            },
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 11, 1, 15, 0, tzinfo=UTC)
        )
        first_revision_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": "19191919-dddd-4ddd-8ddd-191919191919"},
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Revision Replay API Updated",
            },
        )
        replay_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": "19191919-dddd-4ddd-8ddd-191919191919"},
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Revision Replay API Updated",
            },
        )

        assert create_response.status_code == 201
        assert first_revision_response.status_code == 200
        assert replay_response.status_code == 200
        assert replay_response.headers["Cache-Control"] == "no-store"
        assert replay_response.headers["Idempotency-Result-Version"] == "2"
        assert replay_response.headers["Idempotency-Replayed"] == "true"
        assert replay_response.json() == first_revision_response.json()


def test_post_revision_identical_replay_precedes_stale_and_noop_and_returns_200(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("41414141-aaaa-4aaa-8aaa-414141414141")
    audit_event_id = UUID("42424242-bbbb-4bbb-8bbb-424242424242")
    revision_key = "43434343-cccc-4ccc-8ccc-434343434343"
    app = create_app()
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        employer_id, audit_event_id
    )
    with TestClient(app) as client:
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 11, 1, 45, 0, tzinfo=UTC)
        )
        create_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "44444444-dddd-4ddd-8ddd-444444444444"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Replay Precedence Seed",
            },
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 11, 1, 50, 0, tzinfo=UTC)
        )
        first_revision_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": revision_key},
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Replay Precedence Updated",
            },
        )
        receipt_count_before_replay = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count_before_replay = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()
        replay_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": revision_key},
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Replay Precedence Updated",
            },
        )

        receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
        audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

        assert create_response.status_code == 201
        assert first_revision_response.status_code == 200
        assert replay_response.status_code == 200
        assert replay_response.headers["Cache-Control"] == "no-store"
        assert replay_response.headers["Idempotency-Result-Version"] == "2"
        assert replay_response.headers["Idempotency-Replayed"] == "true"
        assert replay_response.json() == first_revision_response.json()
        assert receipt_count_before_replay == 2
        assert audit_event_count_before_replay == 2
        assert receipt_count == receipt_count_before_replay
        assert audit_event_count == audit_event_count_before_replay


def test_post_revision_changed_key_conflict_precedes_stale_and_returns_409(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("45454545-aaaa-4aaa-8aaa-454545454545")
    audit_event_id = UUID("46464646-bbbb-4bbb-8bbb-464646464646")
    revision_key = "47474747-cccc-4ccc-8ccc-474747474747"
    app = create_app()
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        employer_id, audit_event_id
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 11, 1, 55, 0, tzinfo=UTC)
        )
        create_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "48484848-dddd-4ddd-8ddd-484848484848"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Conflict Precedence Seed",
            },
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 11, 2, 0, 0, tzinfo=UTC)
        )
        first_revision_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": revision_key},
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Conflict Precedence Updated",
            },
        )
        receipt_count_before_conflict = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count_before_conflict = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()
        conflict_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": revision_key},
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Conflict Precedence Changed",
            },
        )

        receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
        audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

        assert create_response.status_code == 201
        assert first_revision_response.status_code == 200
        assert first_revision_response.json()["version"] == 2
        assert conflict_response.status_code == 409
        assert conflict_response.headers["Cache-Control"] == "no-store"
        assert conflict_response.json() == {
            "type": "https://golden-rose.local/problems/idempotency-conflict",
            "title": "Conflict",
            "detail": "idempotency conflict",
            "status": 409,
        }
        assert "Synthetic Conflict Precedence" not in conflict_response.text
        assert "Idempotency-Result-Version" not in conflict_response.headers
        assert "Idempotency-Replayed" not in conflict_response.headers
        assert receipt_count_before_conflict == 2
        assert audit_event_count_before_conflict == 2
        assert receipt_count == receipt_count_before_conflict
        assert audit_event_count == audit_event_count_before_conflict


def test_post_revision_fresh_stale_returns_412_without_receipt(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("49494949-aaaa-4aaa-8aaa-494949494949")
    audit_event_id = UUID("50505050-bbbb-4bbb-8bbb-505050505050")
    app = create_app()
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        employer_id, audit_event_id
    )
    app.dependency_overrides[get_clock] = lambda: FixedClock(
        datetime(2026, 8, 11, 2, 5, 0, tzinfo=UTC)
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        create_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "51515151-cccc-4ccc-8ccc-515151515151"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Fresh Stale Seed",
            },
        )
        receipt_count_before_stale = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count_before_stale = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()
        stale_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": "52525252-dddd-4ddd-8ddd-525252525252"},
            json={
                "expected_version": 2,
                "employer_type": "business",
                "display_name": "Synthetic Fresh Stale Updated",
            },
        )

        receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
        audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()
        employer_version = session.execute(
            text("SELECT version FROM employers WHERE employer_id = :employer_id"),
            {"employer_id": str(employer_id)},
        ).scalar_one()

        assert create_response.status_code == 201
        assert receipt_count_before_stale == 1
        assert audit_event_count_before_stale == 1
        assert stale_response.status_code == 412
        assert stale_response.headers["Cache-Control"] == "no-store"
        assert stale_response.json() == {
            "type": "https://golden-rose.local/problems/employer-version-conflict",
            "title": "Precondition Failed",
            "detail": "employer version conflict",
            "status": 412,
        }
        assert "Synthetic Fresh Stale" not in stale_response.text
        assert "Idempotency-Result-Version" not in stale_response.headers
        assert "Idempotency-Replayed" not in stale_response.headers
        assert receipt_count == receipt_count_before_stale
        assert audit_event_count == audit_event_count_before_stale
        assert employer_version == 1


def test_post_revision_fresh_matching_noop_returns_422_without_receipt(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("53535353-aaaa-4aaa-8aaa-535353535353")
    audit_event_id = UUID("54545454-bbbb-4bbb-8bbb-545454545454")
    app = create_app()
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        employer_id, audit_event_id
    )
    app.dependency_overrides[get_clock] = lambda: FixedClock(
        datetime(2026, 8, 11, 2, 10, 0, tzinfo=UTC)
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        create_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "55555555-cccc-4ccc-8ccc-555555555555"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Fresh Noop Seed",
            },
        )
        receipt_count_before_noop = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count_before_noop = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()
        noop_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": "56565656-dddd-4ddd-8ddd-565656565656"},
            json={
                "expected_version": 1,
                "employer_type": "household",
                "display_name": "  Synthetic Fresh Noop Seed  ",
            },
        )

        receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
        audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()
        employer_version = session.execute(
            text("SELECT version FROM employers WHERE employer_id = :employer_id"),
            {"employer_id": str(employer_id)},
        ).scalar_one()

        assert create_response.status_code == 201
        assert receipt_count_before_noop == 1
        assert audit_event_count_before_noop == 1
        assert noop_response.status_code == 422
        assert noop_response.headers["Cache-Control"] == "no-store"
        assert noop_response.json() == {
            "type": "https://golden-rose.local/problems/employer-revision-noop",
            "title": "Unprocessable Entity",
            "detail": "employer revision requires a change",
            "status": 422,
        }
        assert "Synthetic Fresh Noop" not in noop_response.text
        assert "Idempotency-Result-Version" not in noop_response.headers
        assert "Idempotency-Replayed" not in noop_response.headers
        assert receipt_count == receipt_count_before_noop
        assert audit_event_count == audit_event_count_before_noop
        assert employer_version == 1


def test_post_staff_employer_revision_malformed_path_returns_exact_validation_without_writes(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/staff/v1/employers/not-a-uuid/revisions",
            headers={"Idempotency-Key": "57575757-cccc-4ccc-8ccc-575757575757"},
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Malformed Path Value",
            },
        )

        employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
        receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
        audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

        assert response.status_code == 422
        assert response.headers["Cache-Control"] == "no-store"
        assert response.json() == {
            "type": "https://golden-rose.local/problems/request-validation",
            "title": "Unprocessable Entity",
            "detail": "request validation failed",
            "status": 422,
        }
        assert "Synthetic Malformed Path" not in response.text
        assert "not-a-uuid" not in response.text
        assert "Idempotency-Result-Version" not in response.headers
        assert "Idempotency-Replayed" not in response.headers
        assert employer_count == 0
        assert receipt_count == 0
        assert audit_event_count == 0


def test_revision_error_and_exception_diagnostics_are_value_safe(
    clean_tables,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("5a5a5a5a-aaaa-4aaa-8aaa-5a5a5a5a5a5a")
    audit_event_id = UUID("5b5b5b5b-bbbb-4bbb-8bbb-5b5b5b5b5b5b")
    validation_key = "5c5c5c5c-cccc-4ccc-8ccc-5c5c5c5c5c5c"
    success_key = "5d5d5d5d-dddd-4ddd-8ddd-5d5d5d5d5d5d"
    stale_key = "5e5e5e5e-eeee-4eee-8eee-5e5e5e5e5e5e"
    noop_key = "5f5f5f5f-ffff-4fff-8fff-5f5f5f5f5f5f"
    unexpected_key = "6a6a6a6a-aaaa-4aaa-8aaa-6a6a6a6a6a6a"
    app = create_app()
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        employer_id, audit_event_id
    )
    app.dependency_overrides[get_clock] = lambda: FixedClock(
        datetime(2026, 8, 11, 3, 0, 0, tzinfo=UTC)
    )

    validation_secret = (
        "SYNTHETIC_VALIDATION_SECRET SELECT_1 "
        "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose "
        "RAW_RESPONSE_BODY_SECRET"
    )

    def assert_value_safe(response, *forbidden_values: str) -> None:
        assert response.headers["Cache-Control"] == "no-store"
        for forbidden_value in forbidden_values:
            assert forbidden_value not in response.text

    with TestClient(app, raise_server_exceptions=False) as client:
        create_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "69696969-bbbb-4bbb-8bbb-696969696969"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Diagnostic Seed",
            },
        )

        validation_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": validation_key},
            json={
                "employer_type": "business",
                "display_name": validation_secret,
            },
        )

        success_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": success_key},
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Diagnostic Updated",
            },
        )

        conflict_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": success_key},
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Conflict Diagnostic Secret",
            },
        )

        stale_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": stale_key},
            json={
                "expected_version": 1,
                "employer_type": "household",
                "display_name": "Synthetic Stale Diagnostic Secret",
            },
        )

        noop_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": noop_key},
            json={
                "expected_version": 2,
                "employer_type": "business",
                "display_name": "  Synthetic Diagnostic Updated  ",
            },
        )

        def raise_unexpected_revision_error(**_: object) -> None:
            raise RuntimeError(
                "SYNTHETIC_EXCEPTION_SECRET SELECT * FROM employers "
                "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose "
                "RAW_RESPONSE_BODY_SECRET"
            )

        monkeypatch.setattr(
            employers_module,
            "revise_draft_employer",
            raise_unexpected_revision_error,
        )

        unexpected_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": unexpected_key},
            json={
                "expected_version": 2,
                "employer_type": "business",
                "display_name": "Synthetic Unexpected Diagnostic Secret",
            },
        )

        assert create_response.status_code == 201
        assert validation_response.status_code == 422
        assert validation_response.json() == {
            "type": "https://golden-rose.local/problems/request-validation",
            "title": "Unprocessable Entity",
            "detail": "request validation failed",
            "status": 422,
        }
        assert_value_safe(
            validation_response,
            validation_secret,
            validation_key,
            "SELECT_1",
            "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
            "RAW_RESPONSE_BODY_SECRET",
        )

        assert success_response.status_code == 200
        assert conflict_response.status_code == 409
        assert conflict_response.json() == {
            "type": "https://golden-rose.local/problems/idempotency-conflict",
            "title": "Conflict",
            "detail": "idempotency conflict",
            "status": 409,
        }
        assert_value_safe(
            conflict_response,
            "Synthetic Conflict Diagnostic Secret",
            success_key,
        )

        assert stale_response.status_code == 412
        assert stale_response.json() == {
            "type": "https://golden-rose.local/problems/employer-version-conflict",
            "title": "Precondition Failed",
            "detail": "employer version conflict",
            "status": 412,
        }
        assert_value_safe(
            stale_response,
            "Synthetic Stale Diagnostic Secret",
            stale_key,
        )

        assert noop_response.status_code == 422
        assert noop_response.json() == {
            "type": "https://golden-rose.local/problems/employer-revision-noop",
            "title": "Unprocessable Entity",
            "detail": "employer revision requires a change",
            "status": 422,
        }
        assert_value_safe(
            noop_response,
            "Synthetic Diagnostic Updated",
            noop_key,
        )

        assert unexpected_response.status_code == 500
        assert unexpected_response.json() == {
            "type": "https://golden-rose.local/problems/internal-error",
            "title": "Internal Server Error",
            "detail": "internal server error",
            "status": 500,
        }
        assert_value_safe(
            unexpected_response,
            "Synthetic Unexpected Diagnostic Secret",
            unexpected_key,
            "SYNTHETIC_EXCEPTION_SECRET",
            "SELECT * FROM employers",
            "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
            "RAW_RESPONSE_BODY_SECRET",
        )


def test_post_staff_employer_revision_denial_precedes_record_and_writes(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    app = create_app()
    app.dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
        actor_id=UUID("58585858-aaaa-4aaa-8aaa-585858585858"),
        role_name="synthetic_staff_without_revision",
        permissions=frozenset(),
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/staff/v1/employers/59595959-bbbb-4bbb-8bbb-595959595959/revisions",
            headers={"Idempotency-Key": "60606060-cccc-4ccc-8ccc-606060606060"},
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Denied Revision Value",
            },
        )

        employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
        receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
        audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

        assert response.status_code == 403
        assert response.headers["Cache-Control"] == "no-store"
        assert response.json() == {
            "type": "https://golden-rose.local/problems/forbidden",
            "title": "Forbidden",
            "detail": "forbidden",
            "status": 403,
        }
        assert "Synthetic Denied Revision" not in response.text
        assert "59595959" not in response.text
        assert "Idempotency-Result-Version" not in response.headers
        assert "Idempotency-Replayed" not in response.headers
        assert employer_count == 0
        assert receipt_count == 0
        assert audit_event_count == 0


def test_post_staff_employer_revision_ignores_actor_role_permission_headers(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    synthetic_actor_id = UUID("22222222-2222-4222-8222-222222222222")
    spoofed_actor_id = UUID("61616161-aaaa-4aaa-8aaa-616161616161")
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", str(synthetic_actor_id))

    employer_id = UUID("62626262-bbbb-4bbb-8bbb-626262626262")
    audit_event_id = UUID("63636363-cccc-4ccc-8ccc-636363636363")
    app = create_app()
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        employer_id, audit_event_id
    )
    with TestClient(app) as client:
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 11, 2, 15, 0, tzinfo=UTC)
        )
        create_response = client.post(
            "/api/staff/v1/employers",
            headers={
                "Idempotency-Key": "64646464-dddd-4ddd-8ddd-646464646464",
                "X-Staff-Actor-Id": str(spoofed_actor_id),
                "X-Staff-Role": "platform_admin",
                "X-Staff-Permissions": "*",
            },
            json={
                "employer_type": "household",
                "display_name": "Synthetic Header Authority Seed",
            },
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 11, 2, 20, 0, tzinfo=UTC)
        )
        revision_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={
                "Idempotency-Key": "65656565-eeee-4eee-8eee-656565656565",
                "X-Staff-Actor-Id": str(spoofed_actor_id),
                "X-Staff-Role": "platform_admin",
                "X-Staff-Permissions": "*",
            },
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Header Authority Updated",
            },
        )

        employer_actor_row = session.execute(
            text("SELECT created_by, updated_by FROM employers WHERE employer_id = :employer_id"),
            {"employer_id": str(employer_id)},
        ).one()
        revision_audit_actor_id = session.execute(
            text(
                "SELECT actor_id FROM audit_events "
                "WHERE command_id = :command_id AND event_type = 'employer.draft_revised'"
            ),
            {"command_id": "65656565-eeee-4eee-8eee-656565656565"},
        ).scalar_one()

        assert create_response.status_code == 201
        assert revision_response.status_code == 200
        assert revision_response.headers["Cache-Control"] == "no-store"
        assert revision_response.json()["version"] == 2
        assert str(employer_actor_row.created_by) == str(synthetic_actor_id)
        assert str(employer_actor_row.updated_by) == str(synthetic_actor_id)
        assert str(revision_audit_actor_id) == str(synthetic_actor_id)
        assert str(spoofed_actor_id) not in {
            str(employer_actor_row.created_by),
            str(employer_actor_row.updated_by),
            str(revision_audit_actor_id),
        }


def test_post_staff_employer_revision_replay_after_later_revision_returns_current_truth_and_original_result_version_without_writes(  # noqa: E501
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("20202020-aaaa-4aaa-8aaa-202020202020")
    audit_event_id = UUID("21212121-bbbb-4bbb-8bbb-212121212121")
    first_revision_key = "22222222-cccc-4ccc-8ccc-222222222222"
    app = create_app()
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        employer_id, audit_event_id
    )
    with TestClient(app) as client:
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 11, 1, 20, 0, tzinfo=UTC)
        )
        create_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "23232323-dddd-4ddd-8ddd-232323232323"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Revision Later API Seed",
            },
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 11, 1, 25, 0, tzinfo=UTC)
        )
        first_revision_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": first_revision_key},
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Revision Later API v2",
            },
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 11, 1, 30, 0, tzinfo=UTC)
        )
        later_revision_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": "24242424-eeee-4eee-8eee-242424242424"},
            json={
                "expected_version": 2,
                "employer_type": "household",
                "display_name": "Synthetic Revision Later API v3",
            },
        )
        command_receipt_count_before_replay = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count_before_replay = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()
        replay_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": first_revision_key},
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Revision Later API v2",
            },
        )

        command_receipt_count = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

        assert create_response.status_code == 201
        assert first_revision_response.status_code == 200
        assert first_revision_response.headers["Idempotency-Result-Version"] == "2"
        assert later_revision_response.status_code == 200
        assert later_revision_response.headers["Idempotency-Result-Version"] == "3"
        assert replay_response.status_code == 200
        assert replay_response.headers["Cache-Control"] == "no-store"
        assert replay_response.headers["Idempotency-Result-Version"] == "2"
        assert replay_response.headers["Idempotency-Replayed"] == "true"
        assert replay_response.json() == {
            "employer_id": str(employer_id),
            "employer_type": "household",
            "display_name": "Synthetic Revision Later API v3",
            "lifecycle_status": "draft",
            "source_channel": "staff_entry",
            "version": 3,
            "received_at": "2026-08-11T01:20:00Z",
            "created_at": "2026-08-11T01:20:00Z",
            "updated_at": "2026-08-11T01:30:00Z",
        }
        assert command_receipt_count_before_replay == 3
        assert audit_event_count_before_replay == 3
        assert command_receipt_count == command_receipt_count_before_replay
        assert audit_event_count == audit_event_count_before_replay


def test_post_staff_employer_revision_maps_bounded_failure_matrix_without_values(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("25252525-aaaa-4aaa-8aaa-252525252525")
    audit_event_id = UUID("26262626-bbbb-4bbb-8bbb-262626262626")
    app = create_app()
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        employer_id, audit_event_id
    )
    app.dependency_overrides[get_clock] = lambda: FixedClock(
        datetime(2026, 8, 11, 1, 35, 0, tzinfo=UTC)
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        create_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "27272727-cccc-4ccc-8ccc-272727272727"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Revision Failure Seed",
            },
        )
        assert create_response.status_code == 201

        cases = [
            (
                "invalid key",
                "/api/staff/v1/employers/25252525-aaaa-4aaa-8aaa-252525252525/revisions",
                {"Idempotency-Key": "not-a-uuid"},
                {
                    "expected_version": 1,
                    "employer_type": "business",
                    "display_name": "Synthetic Revision Failure Value",
                },
                400,
                {
                    "type": "https://golden-rose.local/problems/invalid-idempotency-key",
                    "title": "Bad Request",
                    "detail": "invalid idempotency key",
                    "status": 400,
                },
            ),
            (
                "missing employer",
                "/api/staff/v1/employers/28282828-dddd-4ddd-8ddd-282828282828/revisions",
                {"Idempotency-Key": "29292929-eeee-4eee-8eee-292929292929"},
                {
                    "expected_version": 1,
                    "employer_type": "business",
                    "display_name": "Synthetic Revision Failure Value",
                },
                404,
                {
                    "type": "https://golden-rose.local/problems/employer-not-found",
                    "title": "Not Found",
                    "detail": "employer not found",
                    "status": 404,
                },
            ),
            (
                "stale",
                "/api/staff/v1/employers/25252525-aaaa-4aaa-8aaa-252525252525/revisions",
                {"Idempotency-Key": "30303030-ffff-4fff-8fff-303030303030"},
                {
                    "expected_version": 2,
                    "employer_type": "business",
                    "display_name": "Synthetic Revision Failure Value",
                },
                412,
                {
                    "type": "https://golden-rose.local/problems/employer-version-conflict",
                    "title": "Precondition Failed",
                    "detail": "employer version conflict",
                    "status": 412,
                },
            ),
            (
                "noop",
                "/api/staff/v1/employers/25252525-aaaa-4aaa-8aaa-252525252525/revisions",
                {"Idempotency-Key": "31313131-abab-4bab-8bab-313131313131"},
                {
                    "expected_version": 1,
                    "employer_type": "household",
                    "display_name": "Synthetic Revision Failure Seed",
                },
                422,
                {
                    "type": "https://golden-rose.local/problems/employer-revision-noop",
                    "title": "Unprocessable Entity",
                    "detail": "employer revision requires a change",
                    "status": 422,
                },
            ),
            (
                "validation",
                "/api/staff/v1/employers/25252525-aaaa-4aaa-8aaa-252525252525/revisions",
                {"Idempotency-Key": "32323232-bcbc-4cbc-8cbc-323232323232"},
                {
                    "expected_version": True,
                    "employer_type": "business",
                    "display_name": "Synthetic Revision Failure Value",
                    "updated_by": "forbidden",
                },
                422,
                {
                    "type": "https://golden-rose.local/problems/request-validation",
                    "title": "Unprocessable Entity",
                    "detail": "request validation failed",
                    "status": 422,
                },
            ),
        ]

        for label, path, headers, body, status_code, expected_problem in cases:
            response = client.post(path, headers=headers, json=body)

            assert response.status_code == status_code, label
            assert response.headers["Cache-Control"] == "no-store"
            assert response.json() == expected_problem
            assert "Idempotency-Result-Version" not in response.headers
            assert "Idempotency-Replayed" not in response.headers
            assert "Synthetic Revision Failure" not in response.text

        conflict_key = "33333333-cdcd-4dcd-8dcd-333333333333"
        success_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": conflict_key},
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Revision Conflict Success",
            },
        )
        conflict_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": conflict_key},
            json={
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Revision Conflict Value",
            },
        )

        assert success_response.status_code == 200
        assert conflict_response.status_code == 409
        assert conflict_response.headers["Cache-Control"] == "no-store"
        assert conflict_response.json() == {
            "type": "https://golden-rose.local/problems/idempotency-conflict",
            "title": "Conflict",
            "detail": "idempotency conflict",
            "status": 409,
        }
        assert "Synthetic Revision Conflict" not in conflict_response.text
        assert "Idempotency-Result-Version" not in conflict_response.headers
        assert "Idempotency-Replayed" not in conflict_response.headers

        unavailable_marker = "Synthetic Revision Persistence Value"

        def raise_safe_persistence_error(**_: object):
            raise SafePersistenceError(f"persistence operation failed {unavailable_marker}")

        monkeypatch.setattr(
            employers_module,
            "revise_draft_employer",
            raise_safe_persistence_error,
        )
        unavailable_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": "34343434-dede-4ede-8ede-343434343434"},
            json={
                "expected_version": 2,
                "employer_type": "household",
                "display_name": unavailable_marker,
            },
        )

        def raise_unexpected_error(**_: object):
            raise RuntimeError("Synthetic Revision Unexpected Value")

        monkeypatch.setattr(
            employers_module,
            "revise_draft_employer",
            raise_unexpected_error,
        )
        unexpected_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": "35353535-efef-4fef-8fef-353535353535"},
            json={
                "expected_version": 2,
                "employer_type": "household",
                "display_name": "Synthetic Revision Unexpected Value",
            },
        )

        assert unavailable_response.status_code == 503
        assert unavailable_response.headers["Cache-Control"] == "no-store"
        assert unavailable_response.json() == {
            "type": "https://golden-rose.local/problems/service-unavailable",
            "title": "Service Unavailable",
            "detail": "service unavailable",
            "status": 503,
        }
        assert unavailable_marker not in unavailable_response.text
        assert unexpected_response.status_code == 500
        assert unexpected_response.headers["Cache-Control"] == "no-store"
        assert unexpected_response.json() == {
            "type": "https://golden-rose.local/problems/internal-error",
            "title": "Internal Server Error",
            "detail": "internal server error",
            "status": 500,
        }
        assert "Synthetic Revision Unexpected Value" not in unexpected_response.text

        employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
        assert employer_count == 1


def test_post_staff_employer_revision_returns_exact_noop_and_version_conflict_problem_contracts(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("36363636-aaaa-4aaa-8aaa-363636363636")
    audit_event_id = UUID("37373737-bbbb-4bbb-8bbb-373737373737")
    app = create_app()
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        employer_id, audit_event_id
    )
    app.dependency_overrides[get_clock] = lambda: FixedClock(
        datetime(2026, 8, 11, 1, 40, 0, tzinfo=UTC)
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        create_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "38383838-cccc-4ccc-8ccc-383838383838"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Noop Conflict Seed",
            },
        )
        noop_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": "39393939-dddd-4ddd-8ddd-393939393939"},
            json={
                "expected_version": 1,
                "employer_type": "household",
                "display_name": "  Synthetic Noop Conflict Seed  ",
            },
        )
        version_conflict_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/revisions",
            headers={"Idempotency-Key": "40404040-eeee-4eee-8eee-404040404040"},
            json={
                "expected_version": 2,
                "employer_type": "business",
                "display_name": "Synthetic Noop Conflict Updated",
            },
        )

        employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
        receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
        audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

        assert create_response.status_code == 201
        assert noop_response.status_code == 422
        assert noop_response.headers["Cache-Control"] == "no-store"
        assert noop_response.json() == {
            "type": "https://golden-rose.local/problems/employer-revision-noop",
            "title": "Unprocessable Entity",
            "detail": "employer revision requires a change",
            "status": 422,
        }
        assert "Synthetic Noop Conflict" not in noop_response.text
        assert "Idempotency-Result-Version" not in noop_response.headers
        assert "Idempotency-Replayed" not in noop_response.headers

        assert version_conflict_response.status_code == 412
        assert version_conflict_response.headers["Cache-Control"] == "no-store"
        assert version_conflict_response.json() == {
            "type": "https://golden-rose.local/problems/employer-version-conflict",
            "title": "Precondition Failed",
            "detail": "employer version conflict",
            "status": 412,
        }
        assert "Synthetic Noop Conflict" not in version_conflict_response.text
        assert "Idempotency-Result-Version" not in version_conflict_response.headers
        assert "Idempotency-Replayed" not in version_conflict_response.headers

        assert employer_count == 1
        assert receipt_count == 1
        assert audit_event_count == 1


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
    with TestClient(app) as client:
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
        assert first_response.headers["Cache-Control"] == "no-store"
        assert second_response.headers["Cache-Control"] == "no-store"
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
    with TestClient(app) as client:
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
    with TestClient(app) as client:
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

    with TestClient(create_app()) as client:
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

    with TestClient(create_app()) as client:
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
    with TestClient(app) as client:
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
    with TestClient(create_app(), raise_server_exceptions=False) as client:
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
    with TestClient(create_app(), raise_server_exceptions=False) as client:
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


def test_existing_create_failure_matrix_media_cache_body_headers_and_write_authority_remains_exact(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    with TestClient(create_app(), raise_server_exceptions=False) as client:
        cases = [
            (
                "invalid-idempotency-key",
                {"Idempotency-Key": "not-a-uuid"},
                {
                    "employer_type": "household",
                    "display_name": "Synthetic Create Invalid Value",
                },
                400,
                {
                    "type": "https://golden-rose.local/problems/invalid-idempotency-key",
                    "title": "Bad Request",
                    "detail": "invalid idempotency key",
                    "status": 400,
                },
            ),
            (
                "request-validation",
                {"Idempotency-Key": "74747474-aaaa-4aaa-8aaa-747474747474"},
                {
                    "employer_type": "invalid",
                    "display_name": "Synthetic Create Validation Value",
                    "created_by": "forbidden",
                },
                422,
                {
                    "type": "https://golden-rose.local/problems/request-validation",
                    "title": "Unprocessable Entity",
                    "detail": "request validation failed",
                    "status": 422,
                },
            ),
        ]

        for label, headers, body, status_code, expected_problem in cases:
            response = client.post("/api/staff/v1/employers", headers=headers, json=body)

            assert response.status_code == status_code, label
            assert response.headers["Content-Type"] == "application/json"
            assert response.headers["Cache-Control"] == "no-store"
            assert response.json() == expected_problem
            assert "Idempotency-Result-Version" not in response.headers
            assert "Idempotency-Replayed" not in response.headers
            assert "Synthetic Create" not in response.text

        denied_app = create_app()
        denied_app.dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
            actor_id=UUID("75757575-bbbb-4bbb-8bbb-757575757575"),
            role_name="synthetic_staff_without_create",
            permissions=frozenset(),
        )
        with TestClient(denied_app, raise_server_exceptions=False) as denied_client:
            denied_response = denied_client.post(
                "/api/staff/v1/employers",
                headers={"Idempotency-Key": "76767676-cccc-4ccc-8ccc-767676767676"},
                json={
                    "employer_type": "household",
                    "display_name": "Synthetic Create Denied Value",
                },
            )

        assert denied_response.status_code == 403
        assert denied_response.headers["Content-Type"] == "application/json"
        assert denied_response.headers["Cache-Control"] == "no-store"
        assert denied_response.json() == {
            "type": "https://golden-rose.local/problems/forbidden",
            "title": "Forbidden",
            "detail": "forbidden",
            "status": 403,
        }
        assert "Synthetic Create Denied" not in denied_response.text
        assert "Idempotency-Result-Version" not in denied_response.headers
        assert "Idempotency-Replayed" not in denied_response.headers

        conflict_key = "77777777-dddd-4ddd-8ddd-777777777777"
        first_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": conflict_key},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Create Conflict Seed",
            },
        )
        receipt_count_before_conflict = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count_before_conflict = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()
        conflict_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": conflict_key},
            json={
                "employer_type": "business",
                "display_name": "Synthetic Create Conflict Value",
            },
        )
        receipt_count_after_conflict = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count_after_conflict = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()

        assert first_response.status_code == 201
        assert first_response.headers["Idempotency-Result-Version"] == "1"
        assert conflict_response.status_code == 409
        assert conflict_response.headers["Content-Type"] == "application/json"
        assert conflict_response.headers["Cache-Control"] == "no-store"
        assert conflict_response.json() == {
            "type": "https://golden-rose.local/problems/idempotency-conflict",
            "title": "Conflict",
            "detail": "idempotency conflict",
            "status": 409,
        }
        assert "Synthetic Create Conflict" not in conflict_response.text
        assert "Idempotency-Result-Version" not in conflict_response.headers
        assert "Idempotency-Replayed" not in conflict_response.headers
        assert receipt_count_before_conflict == 1
        assert audit_event_count_before_conflict == 1
        assert receipt_count_after_conflict == receipt_count_before_conflict
        assert audit_event_count_after_conflict == audit_event_count_before_conflict

    def raise_safe_persistence_error(**_: object):
        raise SafePersistenceError("persistence failed with Synthetic Create Persistence Value")

    monkeypatch.setattr(employers_module, "create_draft_employer", raise_safe_persistence_error)
    with TestClient(create_app(), raise_server_exceptions=False) as unavailable_client:
        unavailable_response = unavailable_client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "78787878-eeee-4eee-8eee-787878787878"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Create Persistence Value",
            },
        )

    assert unavailable_response.status_code == 503
    assert unavailable_response.headers["Content-Type"] == "application/json"
    assert unavailable_response.headers["Cache-Control"] == "no-store"
    assert unavailable_response.json() == {
        "type": "https://golden-rose.local/problems/service-unavailable",
        "title": "Service Unavailable",
        "detail": "service unavailable",
        "status": 503,
    }
    assert "Synthetic Create Persistence" not in unavailable_response.text
    assert "Idempotency-Result-Version" not in unavailable_response.headers
    assert "Idempotency-Replayed" not in unavailable_response.headers

    def raise_unexpected_error(**_: object):
        raise RuntimeError("unexpected Synthetic Create Internal Value")

    monkeypatch.setattr(employers_module, "create_draft_employer", raise_unexpected_error)
    with TestClient(create_app(), raise_server_exceptions=False) as error_client:
        unexpected_response = error_client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "79797979-ffff-4fff-8fff-797979797979"},
            json={
                "employer_type": "business",
                "display_name": "Synthetic Create Internal Value",
            },
        )

    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert unexpected_response.status_code == 500
    assert unexpected_response.headers["Content-Type"] == "application/json"
    assert unexpected_response.headers["Cache-Control"] == "no-store"
    assert unexpected_response.json() == {
        "type": "https://golden-rose.local/problems/internal-error",
        "title": "Internal Server Error",
        "detail": "internal server error",
        "status": 500,
    }
    assert "Synthetic Create Internal" not in unexpected_response.text
    assert "Idempotency-Result-Version" not in unexpected_response.headers
    assert "Idempotency-Replayed" not in unexpected_response.headers
    assert employer_count == 1
    assert receipt_count == 1
    assert audit_event_count == 1


def test_openapi_exposes_only_intended_staff_route() -> None:
    with TestClient(create_app()) as client:
        openapi = client.get("/openapi.json")

        assert openapi.status_code == 200
        paths = openapi.json()["paths"]
        assert set(paths) == {
            "/api/staff/v1/workers/{worker_id}/corrections",
            "/api/staff/v1/workers/{worker_id}/contact/corrections",
            "/api/staff/v1/workers/{worker_id}/residence/corrections",
            "/api/staff/v1/workers/{worker_id}/preferences/corrections",
            "/api/staff/v1/employers/{employer_id}/contacts/{contact_id}/details/corrections",
            "/api/staff/v1/employers/{employer_id}/contacts/{contact_id}/details/address/corrections",
            "/api/staff/v1/employers/{employer_id}/addresses/{address_id}/corrections",
            "/api/staff/v1/employers/{employer_id}/worksites/{worksite_id}/address/corrections",
            "/api/staff/v1/employers/{employer_id}/requests/{request_id}/corrections",
            "/api/staff/v1/canonical-corrections/{event_id}",
            "/api/staff/v1/intake-finalizations/{intake_id}/current-review",
            "/api/staff/v1/intake-finalizations/{intake_id}/current-reviews",
            "/api/staff/v1/intake-finalizations/{intake_id}/current-reviews/{review_id}/restricted",
            "/api/staff/v1/intakes/{intake_id}/links",
            "/api/staff/v1/intakes/{intake_id}/finalizations",
            "/api/staff/v1/workers/query",
            "/api/staff/v1/workers/{worker_id}",
            "/api/staff/v1/workers/{worker_id}/contact",
            "/api/staff/v1/workers/{worker_id}/residence",
            "/api/staff/v1/workers/{worker_id}/preferences",
            "/api/staff/v1/employers/{employer_id}/addresses/query",
            "/api/staff/v1/employers/{employer_id}/worksites/query",
            "/api/staff/v1/employers/{employer_id}/requests/query",
            "/api/staff/v1/employers/{employer_id}/addresses/{address_id}",
            "/api/staff/v1/employers/{employer_id}/worksites/{worksite_id}",
            "/api/staff/v1/employers/{employer_id}/worksites/{worksite_id}/address",
            "/api/staff/v1/employers/{employer_id}/requests/{request_id}",
            "/api/staff/v1/employers/{employer_id}/requests/{request_id}/shift-needs",
            "/api/staff/v1/employers/{employer_id}/requests/{request_id}/shift-needs/query",
            "/api/staff/v1/employers/{employer_id}/requests/{request_id}/shift-needs/{shift_need_id}",
            "/api/staff/v1/employers/{employer_id}/contacts/{contact_id}/details",
            "/api/staff/v1/employers/{employer_id}/contacts/{contact_id}/details/address",
            "/api/staff/v1/intakes/{intake_id}/reviews",
            "/api/staff/v1/intakes/{intake_id}/follow-ups",
            "/api/staff/v1/intakes/{intake_id}/history/query",
            "/api/staff/v1/intakes/{intake_id}/history/{event_id}/restricted",
            "/api/staff/v1/intakes/{intake_id}/follow-up-owners/query",
            "/api/staff/v1/work-interests",
            "/api/staff/v1/work-interests/query",
            "/api/staff/v1/work-interests/{interest_id}/revisions",
            "/api/staff/v1/intakes",
            "/api/staff/v1/intakes/query",
            "/api/staff/v1/intakes/{intake_id}",
            "/api/staff/v1/intakes/{intake_id}/revisions",
            "/api/staff/v1/intakes/{intake_id}/addresses/{section}",
            "/api/staff/v1/intakes/{intake_id}/addresses/{section}/revisions",
            "/api/staff/v1/session",
            "/api/staff/v1/staff-identity-readiness",
            "/api/staff/v1/staff-accounts",
            "/api/staff/v1/staff-accounts/{staff_id}",
            "/api/staff/v1/staff-accounts/{staff_id}/events",
            "/api/staff/v1/staff-accounts/{staff_id}/delegations",
            "/api/staff/v1/staff-accounts/{staff_id}/delegations/{delegation_id}/revoke",
            "/api/staff/v1/staff-accounts/{staff_id}/activate",
            "/api/staff/v1/staff-accounts/{staff_id}/suspend",
            "/api/staff/v1/staff-accounts/{staff_id}/deprovision",
            "/api/staff/v1/staff-accounts/{staff_id}/recovery-evidence",
            "/api/staff/v1/staff-accounts/{staff_id}/session-revocations",
            "/health",
            "/readiness",
            "/api/staff/v1/employers",
            "/api/staff/v1/employers/search",
            "/api/staff/v1/employers/{employer_id}/revisions",
            "/api/staff/v1/employers/{employer_id}",
            "/api/staff/v1/employers/{employer_id}/contacts",
            "/api/staff/v1/employers/{employer_id}/contacts/query",
            "/api/staff/v1/employers/{employer_id}/contacts/{employer_contact_id}",
        }
        assert set(paths["/health"]) == {"get"}
        assert set(paths["/readiness"]) == {"get"}
        assert set(paths["/api/staff/v1/session"]) == {"get"}
        assert set(paths["/api/staff/v1/staff-identity-readiness"]) == {"get"}
        assert set(paths["/api/staff/v1/staff-accounts"]) == {"get", "post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}"]) == {"get"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/events"]) == {"get"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/delegations"]) == {"get", "post"}
        assert set(
            paths["/api/staff/v1/staff-accounts/{staff_id}/delegations/{delegation_id}/revoke"]
        ) == {"post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/activate"]) == {"post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/suspend"]) == {"post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/deprovision"]) == {"post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/recovery-evidence"]) == {"post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/session-revocations"]) == {"post"}
        assert set(paths["/api/staff/v1/employers"]) == {"post"}
        assert set(paths["/api/staff/v1/employers/search"]) == {"post"}
        assert set(paths["/api/staff/v1/employers/{employer_id}/revisions"]) == {"post"}
        assert set(paths["/api/staff/v1/employers/{employer_id}"]) == {"get"}
        assert set(paths["/api/staff/v1/employers/{employer_id}/contacts"]) == {"post"}
        assert set(paths["/api/staff/v1/employers/{employer_id}/contacts/query"]) == {"post"}
        assert set(
            paths["/api/staff/v1/employers/{employer_id}/contacts/{employer_contact_id}"]
        ) == {"get"}
        assert set(
            paths["/api/staff/v1/employers/{employer_id}/requests/{request_id}/shift-needs"]
        ) == {"post"}
        assert set(
            paths["/api/staff/v1/employers/{employer_id}/requests/{request_id}/shift-needs/query"]
        ) == {"post"}
        assert set(
            paths[
                "/api/staff/v1/employers/{employer_id}/requests/{request_id}/shift-needs/{shift_need_id}"
            ]
        ) == {"get"}


def test_openapi_exposes_only_create_search_detail_and_revision_routes() -> None:
    with TestClient(create_app()) as client:
        openapi = client.get("/openapi.json")

        assert openapi.status_code == 200
        paths = openapi.json()["paths"]
        assert set(paths) == {
            "/api/staff/v1/workers/{worker_id}/corrections",
            "/api/staff/v1/workers/{worker_id}/contact/corrections",
            "/api/staff/v1/workers/{worker_id}/residence/corrections",
            "/api/staff/v1/workers/{worker_id}/preferences/corrections",
            "/api/staff/v1/employers/{employer_id}/contacts/{contact_id}/details/corrections",
            "/api/staff/v1/employers/{employer_id}/contacts/{contact_id}/details/address/corrections",
            "/api/staff/v1/employers/{employer_id}/addresses/{address_id}/corrections",
            "/api/staff/v1/employers/{employer_id}/worksites/{worksite_id}/address/corrections",
            "/api/staff/v1/employers/{employer_id}/requests/{request_id}/corrections",
            "/api/staff/v1/canonical-corrections/{event_id}",
            "/api/staff/v1/intake-finalizations/{intake_id}/current-review",
            "/api/staff/v1/intake-finalizations/{intake_id}/current-reviews",
            "/api/staff/v1/intake-finalizations/{intake_id}/current-reviews/{review_id}/restricted",
            "/api/staff/v1/intakes/{intake_id}/links",
            "/api/staff/v1/intakes/{intake_id}/finalizations",
            "/api/staff/v1/workers/query",
            "/api/staff/v1/workers/{worker_id}",
            "/api/staff/v1/workers/{worker_id}/contact",
            "/api/staff/v1/workers/{worker_id}/residence",
            "/api/staff/v1/workers/{worker_id}/preferences",
            "/api/staff/v1/employers/{employer_id}/addresses/query",
            "/api/staff/v1/employers/{employer_id}/worksites/query",
            "/api/staff/v1/employers/{employer_id}/requests/query",
            "/api/staff/v1/employers/{employer_id}/addresses/{address_id}",
            "/api/staff/v1/employers/{employer_id}/worksites/{worksite_id}",
            "/api/staff/v1/employers/{employer_id}/worksites/{worksite_id}/address",
            "/api/staff/v1/employers/{employer_id}/requests/{request_id}",
            "/api/staff/v1/employers/{employer_id}/requests/{request_id}/shift-needs",
            "/api/staff/v1/employers/{employer_id}/requests/{request_id}/shift-needs/query",
            "/api/staff/v1/employers/{employer_id}/requests/{request_id}/shift-needs/{shift_need_id}",
            "/api/staff/v1/employers/{employer_id}/contacts/{contact_id}/details",
            "/api/staff/v1/employers/{employer_id}/contacts/{contact_id}/details/address",
            "/api/staff/v1/intakes/{intake_id}/reviews",
            "/api/staff/v1/intakes/{intake_id}/follow-ups",
            "/api/staff/v1/intakes/{intake_id}/history/query",
            "/api/staff/v1/intakes/{intake_id}/history/{event_id}/restricted",
            "/api/staff/v1/intakes/{intake_id}/follow-up-owners/query",
            "/api/staff/v1/work-interests",
            "/api/staff/v1/work-interests/query",
            "/api/staff/v1/work-interests/{interest_id}/revisions",
            "/api/staff/v1/intakes",
            "/api/staff/v1/intakes/query",
            "/api/staff/v1/intakes/{intake_id}",
            "/api/staff/v1/intakes/{intake_id}/revisions",
            "/api/staff/v1/intakes/{intake_id}/addresses/{section}",
            "/api/staff/v1/intakes/{intake_id}/addresses/{section}/revisions",
            "/api/staff/v1/session",
            "/api/staff/v1/staff-identity-readiness",
            "/api/staff/v1/staff-accounts",
            "/api/staff/v1/staff-accounts/{staff_id}",
            "/api/staff/v1/staff-accounts/{staff_id}/events",
            "/api/staff/v1/staff-accounts/{staff_id}/delegations",
            "/api/staff/v1/staff-accounts/{staff_id}/delegations/{delegation_id}/revoke",
            "/api/staff/v1/staff-accounts/{staff_id}/activate",
            "/api/staff/v1/staff-accounts/{staff_id}/suspend",
            "/api/staff/v1/staff-accounts/{staff_id}/deprovision",
            "/api/staff/v1/staff-accounts/{staff_id}/recovery-evidence",
            "/api/staff/v1/staff-accounts/{staff_id}/session-revocations",
            "/health",
            "/readiness",
            "/api/staff/v1/employers",
            "/api/staff/v1/employers/search",
            "/api/staff/v1/employers/{employer_id}/revisions",
            "/api/staff/v1/employers/{employer_id}",
            "/api/staff/v1/employers/{employer_id}/contacts",
            "/api/staff/v1/employers/{employer_id}/contacts/query",
            "/api/staff/v1/employers/{employer_id}/contacts/{employer_contact_id}",
        }
        assert set(paths["/health"]) == {"get"}
        assert set(paths["/readiness"]) == {"get"}
        assert set(paths["/api/staff/v1/session"]) == {"get"}
        assert set(paths["/api/staff/v1/staff-identity-readiness"]) == {"get"}
        assert set(paths["/api/staff/v1/staff-accounts"]) == {"get", "post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}"]) == {"get"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/events"]) == {"get"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/delegations"]) == {"get", "post"}
        assert set(
            paths["/api/staff/v1/staff-accounts/{staff_id}/delegations/{delegation_id}/revoke"]
        ) == {"post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/activate"]) == {"post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/suspend"]) == {"post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/deprovision"]) == {"post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/recovery-evidence"]) == {"post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/session-revocations"]) == {"post"}
        assert set(paths["/api/staff/v1/employers"]) == {"post"}
        assert set(paths["/api/staff/v1/employers/search"]) == {"post"}
        assert set(paths["/api/staff/v1/employers/{employer_id}"]) == {"get"}
        assert set(paths["/api/staff/v1/employers/{employer_id}/revisions"]) == {"post"}
        assert set(paths["/api/staff/v1/employers/{employer_id}/contacts"]) == {"post"}
        assert set(paths["/api/staff/v1/employers/{employer_id}/contacts/query"]) == {"post"}
        assert set(
            paths["/api/staff/v1/employers/{employer_id}/contacts/{employer_contact_id}"]
        ) == {"get"}


def test_staff_employer_revision_openapi_exposes_only_approved_contract() -> None:
    with TestClient(create_app()) as client:
        openapi = client.get("/openapi.json")

        assert openapi.status_code == 200
        document = openapi.json()
        paths = document["paths"]
        schemas = document["components"]["schemas"]

        assert set(paths) == {
            "/api/staff/v1/workers/{worker_id}/corrections",
            "/api/staff/v1/workers/{worker_id}/contact/corrections",
            "/api/staff/v1/workers/{worker_id}/residence/corrections",
            "/api/staff/v1/workers/{worker_id}/preferences/corrections",
            "/api/staff/v1/employers/{employer_id}/contacts/{contact_id}/details/corrections",
            "/api/staff/v1/employers/{employer_id}/contacts/{contact_id}/details/address/corrections",
            "/api/staff/v1/employers/{employer_id}/addresses/{address_id}/corrections",
            "/api/staff/v1/employers/{employer_id}/worksites/{worksite_id}/address/corrections",
            "/api/staff/v1/employers/{employer_id}/requests/{request_id}/corrections",
            "/api/staff/v1/canonical-corrections/{event_id}",
            "/api/staff/v1/intake-finalizations/{intake_id}/current-review",
            "/api/staff/v1/intake-finalizations/{intake_id}/current-reviews",
            "/api/staff/v1/intake-finalizations/{intake_id}/current-reviews/{review_id}/restricted",
            "/api/staff/v1/intakes/{intake_id}/links",
            "/api/staff/v1/intakes/{intake_id}/finalizations",
            "/api/staff/v1/workers/query",
            "/api/staff/v1/workers/{worker_id}",
            "/api/staff/v1/workers/{worker_id}/contact",
            "/api/staff/v1/workers/{worker_id}/residence",
            "/api/staff/v1/workers/{worker_id}/preferences",
            "/api/staff/v1/employers/{employer_id}/addresses/query",
            "/api/staff/v1/employers/{employer_id}/worksites/query",
            "/api/staff/v1/employers/{employer_id}/requests/query",
            "/api/staff/v1/employers/{employer_id}/addresses/{address_id}",
            "/api/staff/v1/employers/{employer_id}/worksites/{worksite_id}",
            "/api/staff/v1/employers/{employer_id}/worksites/{worksite_id}/address",
            "/api/staff/v1/employers/{employer_id}/requests/{request_id}",
            "/api/staff/v1/employers/{employer_id}/requests/{request_id}/shift-needs",
            "/api/staff/v1/employers/{employer_id}/requests/{request_id}/shift-needs/query",
            "/api/staff/v1/employers/{employer_id}/requests/{request_id}/shift-needs/{shift_need_id}",
            "/api/staff/v1/employers/{employer_id}/contacts/{contact_id}/details",
            "/api/staff/v1/employers/{employer_id}/contacts/{contact_id}/details/address",
            "/api/staff/v1/intakes/{intake_id}/reviews",
            "/api/staff/v1/intakes/{intake_id}/follow-ups",
            "/api/staff/v1/intakes/{intake_id}/history/query",
            "/api/staff/v1/intakes/{intake_id}/history/{event_id}/restricted",
            "/api/staff/v1/intakes/{intake_id}/follow-up-owners/query",
            "/api/staff/v1/work-interests",
            "/api/staff/v1/work-interests/query",
            "/api/staff/v1/work-interests/{interest_id}/revisions",
            "/api/staff/v1/intakes",
            "/api/staff/v1/intakes/query",
            "/api/staff/v1/intakes/{intake_id}",
            "/api/staff/v1/intakes/{intake_id}/revisions",
            "/api/staff/v1/intakes/{intake_id}/addresses/{section}",
            "/api/staff/v1/intakes/{intake_id}/addresses/{section}/revisions",
            "/api/staff/v1/session",
            "/api/staff/v1/staff-identity-readiness",
            "/api/staff/v1/staff-accounts",
            "/api/staff/v1/staff-accounts/{staff_id}",
            "/api/staff/v1/staff-accounts/{staff_id}/events",
            "/api/staff/v1/staff-accounts/{staff_id}/delegations",
            "/api/staff/v1/staff-accounts/{staff_id}/delegations/{delegation_id}/revoke",
            "/api/staff/v1/staff-accounts/{staff_id}/activate",
            "/api/staff/v1/staff-accounts/{staff_id}/suspend",
            "/api/staff/v1/staff-accounts/{staff_id}/deprovision",
            "/api/staff/v1/staff-accounts/{staff_id}/recovery-evidence",
            "/api/staff/v1/staff-accounts/{staff_id}/session-revocations",
            "/health",
            "/readiness",
            "/api/staff/v1/employers",
            "/api/staff/v1/employers/search",
            "/api/staff/v1/employers/{employer_id}/revisions",
            "/api/staff/v1/employers/{employer_id}",
            "/api/staff/v1/employers/{employer_id}/contacts",
            "/api/staff/v1/employers/{employer_id}/contacts/query",
            "/api/staff/v1/employers/{employer_id}/contacts/{employer_contact_id}",
        }
        assert set(paths["/health"]) == {"get"}
        assert set(paths["/readiness"]) == {"get"}
        assert set(paths["/api/staff/v1/session"]) == {"get"}
        assert set(paths["/api/staff/v1/staff-identity-readiness"]) == {"get"}
        assert set(paths["/api/staff/v1/staff-accounts"]) == {"get", "post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}"]) == {"get"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/events"]) == {"get"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/delegations"]) == {"get", "post"}
        assert set(
            paths["/api/staff/v1/staff-accounts/{staff_id}/delegations/{delegation_id}/revoke"]
        ) == {"post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/activate"]) == {"post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/suspend"]) == {"post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/deprovision"]) == {"post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/recovery-evidence"]) == {"post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}/session-revocations"]) == {"post"}
        revision_path = paths["/api/staff/v1/employers/{employer_id}/revisions"]
        assert set(revision_path) == {"post"}
        revision_operation = revision_path["post"]
        assert revision_operation["tags"] == ["staff-employers"]
        assert revision_operation["parameters"] == [
            {
                "name": "employer_id",
                "in": "path",
                "required": True,
                "schema": {"type": "string", "format": "uuid", "title": "Employer Id"},
            },
            {
                "name": "Idempotency-Key",
                "in": "header",
                "required": True,
                "schema": {"type": "string", "title": "Idempotency-Key"},
            },
        ]
        assert revision_operation["requestBody"] == {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ReviseDraftEmployerRequest"}
                }
            },
        }
        assert revision_operation["responses"] == {
            "200": {
                "description": "Successful Response",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/EmployerDetailResponse"}
                    }
                },
            },
            "422": {
                "description": "Validation Error",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/HTTPValidationError"}
                    }
                },
            },
        }

        revision_schema = schemas["ReviseDraftEmployerRequest"]
        assert revision_schema["additionalProperties"] is False
        assert revision_schema["required"] == [
            "expected_version",
            "employer_type",
            "display_name",
        ]
        assert set(revision_schema["properties"]) == {
            "expected_version",
            "employer_type",
            "display_name",
        }
        assert revision_schema["properties"]["expected_version"] == {
            "type": "integer",
            "maximum": 2147483646,
            "minimum": 1,
            "title": "Expected Version",
        }
        assert revision_schema["properties"]["employer_type"] == {
            "type": "string",
            "enum": ["household", "business"],
            "title": "Employer Type",
        }
        assert revision_schema["properties"]["display_name"] == {
            "type": "string",
            "title": "Display Name",
        }

        detail_properties = schemas["EmployerDetailResponse"]["properties"]
        assert "updated_at" in detail_properties
        assert "updated_by" not in detail_properties
