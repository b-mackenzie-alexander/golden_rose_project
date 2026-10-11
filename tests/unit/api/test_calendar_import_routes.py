from collections.abc import Iterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from golden_rose.api.dependencies import get_db_session, get_settings, get_staff_principal
from golden_rose.api.staff import calendar_imports
from golden_rose.application.calendar_imports import (
    CalendarImportCommandResult,
    CalendarImportError,
    CalendarImportNotFoundError,
    CalendarImportSummary,
    CalendarImportVersionConflictError,
    GoogleCalendarEventImport,
)
from golden_rose.application.errors import SafePersistenceError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.config import Settings
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


def configured_oauth_settings() -> Settings:
    return Settings(
        environment="local",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=ACTOR_ID,
        google_calendar_oauth_client_id="calendar-client.apps.googleusercontent.com",
        google_calendar_oauth_client_secret=SecretStr("calendar-secret"),
        google_calendar_oauth_redirect_uri=(
            "http://testserver/api/staff/v1/calendar-imports/oauth/callback"
        ),
    )


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
    assert payload["oauth_connect_available"] is False
    assert payload["connection"]["connection_status"] == "authorization_required"
    assert payload["candidates"][0]["event_title"] == "Owner calendar note"
    assert "provider_event_uid" not in payload["candidates"][0]
    assert "google-private-event-uid" not in response.text
    reader.assert_called_once()


def test_get_calendar_import_summary_reports_oauth_connect_available_when_configured(
    http: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cast(FastAPI, http.app).dependency_overrides[get_settings] = configured_oauth_settings
    monkeypatch.setattr(
        calendar_imports,
        "get_calendar_import_summary",
        Mock(return_value=CalendarImportSummary(connection=None, candidates=())),
    )

    response = http.get("/api/staff/v1/calendar-imports")

    assert response.status_code == 200, response.text
    assert response.json()["oauth_configuration_required"] is False
    assert response.json()["oauth_connect_available"] is True


def test_google_calendar_oauth_start_returns_authorization_url_and_state_cookie(
    http: TestClient,
) -> None:
    cast(FastAPI, http.app).dependency_overrides[get_settings] = configured_oauth_settings

    response = http.post("/api/staff/v1/calendar-imports/oauth/start")

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert "golden_rose_google_calendar_oauth_state=" in response.headers["set-cookie"]
    payload = response.json()
    assert payload["authorization_url"].startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert (
        "scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar.events.readonly"
        in payload["authorization_url"]
    )


def test_google_calendar_oauth_start_requires_calendar_permission(
    http: TestClient,
) -> None:
    cast(FastAPI, http.app).dependency_overrides[get_settings] = configured_oauth_settings
    cast(FastAPI, http.app).dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
        actor_id=ACTOR_ID,
        role_name="viewer",
        permissions=frozenset(),
    )

    response = http.post("/api/staff/v1/calendar-imports/oauth/start")

    assert response.status_code == 403, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["detail"] == "forbidden"


def test_google_calendar_oauth_start_reports_unavailable_when_not_configured(
    http: TestClient,
) -> None:
    response = http.post("/api/staff/v1/calendar-imports/oauth/start")

    assert response.status_code == 503, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["detail"] == "Google Calendar OAuth is not configured"


def test_google_calendar_oauth_callback_imports_events_and_redirects(
    http: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cast(FastAPI, http.app).dependency_overrides[get_settings] = configured_oauth_settings
    observed: dict[str, object] = {}
    monkeypatch.setattr(
        calendar_imports,
        "validate_google_calendar_oauth_state",
        Mock(return_value=SimpleNamespace(staff_id=ACTOR_ID)),
    )
    monkeypatch.setattr(
        calendar_imports,
        "exchange_google_calendar_code",
        Mock(return_value=SimpleNamespace(access_token="access-token", granted_scopes=("scope",))),
    )
    monkeypatch.setattr(calendar_imports, "fetch_google_calendar_events", Mock(return_value=()))
    monkeypatch.setattr(
        calendar_imports,
        "_staff_principal_for_oauth_callback",
        Mock(
            return_value=StaffPrincipal(
                actor_id=ACTOR_ID,
                role_name="owner",
                permissions=frozenset({"calendar_import:manage"}),
            )
        ),
    )

    def import_events(**kwargs):
        observed.update(kwargs)
        return SimpleNamespace(staged_count=0, deduplicated_count=0)

    monkeypatch.setattr(calendar_imports, "import_google_calendar_events", import_events)

    response = http.get(
        "/api/staff/v1/calendar-imports/oauth/callback?code=code&state=state",
        cookies={"golden_rose_google_calendar_oauth_state": "state"},
        follow_redirects=False,
    )

    assert response.status_code == 303, response.text
    assert response.headers["location"] == "/staff/calendar?calendar_import=connected"
    assert response.headers["cache-control"] == "no-store"
    assert cast(StaffPrincipal, observed["principal"]).actor_id == ACTOR_ID


def test_google_calendar_oauth_callback_redirects_failed_without_code(
    http: TestClient,
) -> None:
    cast(FastAPI, http.app).dependency_overrides[get_settings] = configured_oauth_settings

    response = http.get(
        "/api/staff/v1/calendar-imports/oauth/callback?error=access_denied",
        follow_redirects=False,
    )

    assert response.status_code == 303, response.text
    assert response.headers["location"] == "/staff/calendar?calendar_import=failed"
    assert response.headers["cache-control"] == "no-store"


def test_google_calendar_oauth_callback_redirects_failed_when_import_rejected(
    http: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cast(FastAPI, http.app).dependency_overrides[get_settings] = configured_oauth_settings
    monkeypatch.setattr(
        calendar_imports,
        "validate_google_calendar_oauth_state",
        Mock(return_value=SimpleNamespace(staff_id=ACTOR_ID)),
    )
    monkeypatch.setattr(
        calendar_imports,
        "exchange_google_calendar_code",
        Mock(return_value=SimpleNamespace(access_token="access-token", granted_scopes=("scope",))),
    )
    monkeypatch.setattr(
        calendar_imports,
        "fetch_google_calendar_events",
        Mock(
            return_value=(
                GoogleCalendarEventImport(
                    provider_event_uid="event",
                    provider_event_updated_at=NOW,
                    event_title="Calendar event",
                    starts_at=NOW,
                    ends_at=datetime(2026, 10, 9, 15, 0, tzinfo=UTC),
                    time_zone="UTC",
                    location_review=None,
                ),
            )
        ),
    )
    monkeypatch.setattr(
        calendar_imports,
        "_staff_principal_for_oauth_callback",
        Mock(
            return_value=StaffPrincipal(
                actor_id=ACTOR_ID,
                role_name="owner",
                permissions=frozenset({"calendar_import:manage"}),
            )
        ),
    )
    monkeypatch.setattr(
        calendar_imports,
        "import_google_calendar_events",
        Mock(side_effect=CalendarImportError("invalid calendar import")),
    )

    response = http.get(
        "/api/staff/v1/calendar-imports/oauth/callback?code=code&state=state",
        cookies={"golden_rose_google_calendar_oauth_state": "state"},
        follow_redirects=False,
    )

    assert response.status_code == 303, response.text
    assert response.headers["location"] == "/staff/calendar?calendar_import=failed"
    assert response.headers["cache-control"] == "no-store"


def test_staff_principal_for_oauth_callback_requires_active_permitted_staff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        calendar_imports,
        "get_staff_account_by_id",
        Mock(
            return_value=SimpleNamespace(
                staff_id=ACTOR_ID,
                role_name="owner",
                lifecycle_status="active",
                mfa_enrolled=True,
            )
        ),
    )
    monkeypatch.setattr(
        calendar_imports,
        "list_active_staff_permissions",
        Mock(return_value=frozenset({"calendar_import:manage"})),
    )

    principal = calendar_imports._staff_principal_for_oauth_callback(
        session=cast(Any, object()),
        staff_id=ACTOR_ID,
    )

    assert principal.actor_id == ACTOR_ID
    assert "calendar_import:manage" in principal.permissions


@pytest.mark.parametrize(
    ("account", "permissions"),
    [
        (
            SimpleNamespace(
                staff_id=ACTOR_ID,
                role_name="owner",
                lifecycle_status="suspended",
                mfa_enrolled=True,
            ),
            frozenset({"calendar_import:manage"}),
        ),
        (
            SimpleNamespace(
                staff_id=ACTOR_ID,
                role_name="owner",
                lifecycle_status="active",
                mfa_enrolled=False,
            ),
            frozenset({"calendar_import:manage"}),
        ),
        (
            SimpleNamespace(
                staff_id=ACTOR_ID,
                role_name="owner",
                lifecycle_status="active",
                mfa_enrolled=True,
            ),
            frozenset(),
        ),
    ],
)
def test_staff_principal_for_oauth_callback_rejects_ineligible_staff(
    monkeypatch: pytest.MonkeyPatch,
    account: SimpleNamespace,
    permissions: frozenset[str],
) -> None:
    monkeypatch.setattr(calendar_imports, "get_staff_account_by_id", Mock(return_value=account))
    monkeypatch.setattr(
        calendar_imports,
        "list_active_staff_permissions",
        Mock(return_value=permissions),
    )

    with pytest.raises(PermissionError):
        calendar_imports._staff_principal_for_oauth_callback(
            session=cast(Any, object()),
            staff_id=ACTOR_ID,
        )


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
