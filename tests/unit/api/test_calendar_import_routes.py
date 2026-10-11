from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from golden_rose.api.dependencies import get_db_session, get_staff_principal
from golden_rose.api.staff import calendar_imports
from golden_rose.application.calendar_imports import (
    CalendarImportCommandResult,
    CalendarImportError,
    CalendarImportNotFoundError,
    CalendarImportSummary,
    CalendarImportVersionConflictError,
)
from golden_rose.application.errors import SafePersistenceError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.main import create_app
from golden_rose.persistence.external_calendar_imports import (
    ExternalCalendarImportRecord,
    StaffCalendarConnectionRecord,
)

NOW = datetime(2026, 10, 9, 14, 0, tzinfo=UTC)
ACTOR_ID = UUID("11111111-1111-4111-8111-111111111111")
CONNECTION_ID = UUID("22222222-2222-4222-8222-222222222222")
IMPORT_ID = UUID("33333333-3333-4333-8333-333333333333")


@pytest.fixture
def http() -> Iterator[TestClient]:
    app = create_app(engine_factory=lambda: Mock())
    app.dependency_overrides[get_db_session] = lambda: object()
    app.dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
        actor_id=ACTOR_ID,
        role_name="owner",
        permissions=frozenset({"calendar_import:manage"}),
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def connection_record() -> StaffCalendarConnectionRecord:
    return StaffCalendarConnectionRecord(
        connection_id=CONNECTION_ID,
        staff_id=ACTOR_ID,
        provider_name="google_calendar",
        calendar_alias="primary",
        token_material_ref=None,
        granted_scopes=[],
        connection_status="authorization_required",
        connected_at=None,
        disconnected_at=None,
        last_sync_status="configuration_required",
        last_sync_error="oauth_configuration_pending",
        created_at=NOW,
        created_by=ACTOR_ID,
        updated_at=NOW,
        updated_by=ACTOR_ID,
        version=1,
    )


def candidate_record(
    *,
    status: str = "candidate",
    version: int = 1,
) -> ExternalCalendarImportRecord:
    return ExternalCalendarImportRecord(
        import_id=IMPORT_ID,
        connection_id=CONNECTION_ID,
        provider_event_uid="google-private-event-uid",
        provider_event_updated_at=NOW,
        event_title="Owner calendar note",
        starts_at=datetime(2026, 10, 12, 13, 30, tzinfo=UTC),
        ends_at=datetime(2026, 10, 12, 14, 0, tzinfo=UTC),
        time_zone="America/New_York",
        location_review="Queens",
        import_status=status,  # type: ignore[arg-type]
        linked_entity_type=None,
        linked_entity_id=None,
        created_at=NOW,
        created_by=ACTOR_ID,
        updated_at=NOW,
        updated_by=ACTOR_ID,
        version=version,
    )


def command_headers() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid4())}


def test_get_calendar_import_summary_is_no_store_and_value_safe(
    http: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reader = Mock(
        return_value=CalendarImportSummary(
            connection=connection_record(),
            candidates=(candidate_record(),),
        )
    )
    monkeypatch.setattr(calendar_imports, "get_calendar_import_summary", reader)

    response = http.get("/api/staff/v1/calendar-imports")

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    payload = response.json()
    assert payload["oauth_configuration_required"] is True
    assert payload["connection"]["connection_status"] == "authorization_required"
    assert payload["candidates"][0]["event_title"] == "Owner calendar note"
    assert "provider_event_uid" not in payload["candidates"][0]
    assert "google-private-event-uid" not in response.text
    reader.assert_called_once()


@pytest.mark.parametrize(
    ("side_effect", "expected_status", "expected_detail"),
    [
        (PermissionError("calendar_import:manage"), 403, "forbidden"),
        (SafePersistenceError("private database value"), 503, "service unavailable"),
    ],
)
def test_get_calendar_import_summary_maps_safe_errors(
    http: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    side_effect: Exception,
    expected_status: int,
    expected_detail: str,
) -> None:
    monkeypatch.setattr(
        calendar_imports,
        "get_calendar_import_summary",
        Mock(side_effect=side_effect),
    )

    response = http.get("/api/staff/v1/calendar-imports")

    assert response.status_code == expected_status, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["detail"] == expected_detail


def test_stage_calendar_candidate_returns_command_result_without_provider_uid(
    http: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    staged = Mock(
        return_value=CalendarImportCommandResult(
            candidate=candidate_record(),
            event_type="external_calendar.candidate_imported",
            result_version=1,
            replayed=False,
        )
    )
    monkeypatch.setattr(calendar_imports, "stage_external_calendar_candidate", staged)

    response = http.post(
        "/api/staff/v1/calendar-imports/candidates",
        headers=command_headers(),
        json={
            "provider_event_uid": "google-private-event-uid",
            "provider_event_updated_at": "2026-10-09T14:00:00Z",
            "event_title": "Owner calendar note",
            "starts_at": "2026-10-12T13:30:00Z",
            "ends_at": "2026-10-12T14:00:00Z",
            "time_zone": "America/New_York",
            "location_review": "Queens",
            "reason_text": "Staff reviewed owner calendar import preview",
        },
    )

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["idempotency-result-version"] == "1"
    payload = response.json()
    assert payload["event_type"] == "external_calendar.candidate_imported"
    assert payload["candidate"]["import_status"] == "candidate"
    assert "provider_event_uid" not in payload["candidate"]
    assert "google-private-event-uid" not in response.text
    assert staged.call_args.kwargs["provider_event_uid"] == "google-private-event-uid"
    assert staged.call_args.kwargs["principal"].actor_id == ACTOR_ID


def test_stage_calendar_candidate_maps_invalid_request_to_no_store_problem(
    http: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        calendar_imports,
        "stage_external_calendar_candidate",
        Mock(side_effect=CalendarImportError("external event interval is invalid")),
    )

    response = http.post(
        "/api/staff/v1/calendar-imports/candidates",
        headers=command_headers(),
        json={
            "provider_event_uid": "google-private-event-uid",
            "provider_event_updated_at": "2026-10-09T14:00:00Z",
            "event_title": "Owner calendar note",
            "starts_at": "2026-10-12T14:00:00Z",
            "ends_at": "2026-10-12T13:30:00Z",
            "time_zone": "America/New_York",
            "reason_text": "Staff reviewed owner calendar import preview",
        },
    )

    assert response.status_code == 422, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["detail"] == "calendar import request is invalid"


def test_dispose_calendar_candidate_maps_version_conflict_to_no_store_problem(
    http: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    disposer = Mock(
        side_effect=CalendarImportVersionConflictError(
            "external calendar candidate version conflict"
        )
    )
    monkeypatch.setattr(calendar_imports, "dispose_external_calendar_candidate", disposer)

    response = http.post(
        f"/api/staff/v1/calendar-imports/candidates/{IMPORT_ID}/ignore",
        headers=command_headers(),
        json={
            "expected_version": 1,
            "reason_text": "Duplicate of an existing Golden Rose item",
        },
    )

    assert response.status_code == 412, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["detail"] == "calendar import candidate version conflict"


def test_dispose_calendar_candidate_maps_missing_candidate_to_no_store_problem(
    http: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        calendar_imports,
        "dispose_external_calendar_candidate",
        Mock(side_effect=CalendarImportNotFoundError("missing")),
    )

    response = http.post(
        f"/api/staff/v1/calendar-imports/candidates/{IMPORT_ID}/ignore",
        headers=command_headers(),
        json={
            "expected_version": 1,
            "reason_text": "Duplicate of an existing Golden Rose item",
        },
    )

    assert response.status_code == 404, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["detail"] == "calendar import candidate not found"


def test_mark_existing_calendar_candidate_returns_command_result(
    http: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    disposer = Mock(
        return_value=CalendarImportCommandResult(
            candidate=candidate_record(status="marked_existing", version=2),
            event_type="external_calendar.candidate_marked_existing",
            result_version=2,
            replayed=False,
        )
    )
    monkeypatch.setattr(calendar_imports, "dispose_external_calendar_candidate", disposer)

    response = http.post(
        f"/api/staff/v1/calendar-imports/candidates/{IMPORT_ID}/mark-existing",
        headers=command_headers(),
        json={
            "expected_version": 1,
            "reason_text": "Already represented in Golden Rose",
        },
    )

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["idempotency-result-version"] == "2"
    payload = response.json()
    assert payload["event_type"] == "external_calendar.candidate_marked_existing"
    assert payload["candidate"]["import_status"] == "marked_existing"
    assert disposer.call_args.kwargs["disposition"] == "marked_existing"
