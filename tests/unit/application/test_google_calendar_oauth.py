import hashlib
import hmac
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import pytest
from pydantic import SecretStr

from golden_rose.application import google_calendar_oauth as calendar_oauth
from golden_rose.application.calendar_imports import GOOGLE_CALENDAR_EVENTS_READONLY_SCOPE
from golden_rose.application.google_calendar_oauth import (
    GOOGLE_CALENDAR_LOCATION_REVIEW,
    GOOGLE_EVENTS_URL,
    GOOGLE_TOKEN_URL,
    GoogleCalendarOAuthError,
    build_google_calendar_oauth_start,
    exchange_google_calendar_code,
    fetch_google_calendar_events,
    validate_google_calendar_oauth_state,
)
from golden_rose.config import Settings

NOW = datetime(2026, 10, 11, 21, 0, tzinfo=UTC)
STAFF_ID = UUID("11111111-1111-4111-8111-111111111111")


class _Response:
    def __init__(
        self,
        payload: Any,
        *,
        content_type: str = "application/json; charset=utf-8",
    ) -> None:
        self._payload = payload
        self.headers = {"Content-Type": content_type}

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def settings() -> Settings:
    return Settings(
        environment="local",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=STAFF_ID,
        google_calendar_oauth_client_id="calendar-client.apps.googleusercontent.com",
        google_calendar_oauth_client_secret=SecretStr("calendar-secret"),
        google_calendar_oauth_redirect_uri=(
            "http://testserver/api/staff/v1/calendar-imports/oauth/callback"
        ),
    )


def test_google_calendar_oauth_state_round_trips_with_authorization_url() -> None:
    start = build_google_calendar_oauth_start(settings=settings(), staff_id=STAFF_ID, now=NOW)

    assert start.authorization_url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    query = parse_qs(urlparse(start.authorization_url).query)
    assert query["scope"] == [GOOGLE_CALENDAR_EVENTS_READONLY_SCOPE]

    decoded = validate_google_calendar_oauth_state(
        settings=settings(),
        state=start.state,
        cookie_state=start.state,
        now=NOW,
    )

    assert decoded.staff_id == STAFF_ID


def test_google_calendar_oauth_state_rejects_cookie_mismatch() -> None:
    start = build_google_calendar_oauth_start(settings=settings(), staff_id=STAFF_ID, now=NOW)

    with pytest.raises(GoogleCalendarOAuthError, match="state is invalid"):
        validate_google_calendar_oauth_state(
            settings=settings(),
            state=start.state,
            cookie_state="different",
            now=NOW,
        )


def test_google_calendar_oauth_state_rejects_expired_and_tampered_values() -> None:
    start = build_google_calendar_oauth_start(settings=settings(), staff_id=STAFF_ID, now=NOW)

    with pytest.raises(GoogleCalendarOAuthError, match="state expired"):
        validate_google_calendar_oauth_state(
            settings=settings(),
            state=start.state,
            cookie_state=start.state,
            now=NOW + timedelta(seconds=601),
        )
    tampered = f"{start.state[:-1]}x"
    with pytest.raises(GoogleCalendarOAuthError, match="state signature is invalid"):
        validate_google_calendar_oauth_state(
            settings=settings(),
            state=tampered,
            cookie_state=tampered,
            now=NOW,
        )
    with pytest.raises(GoogleCalendarOAuthError, match="state is invalid"):
        validate_google_calendar_oauth_state(
            settings=settings(),
            state="not-a-signed-state",
            cookie_state="not-a-signed-state",
            now=NOW,
        )


def test_google_calendar_oauth_state_rejects_signed_invalid_payload() -> None:
    body = calendar_oauth._base64url(b'{"staff_id": "not-a-uuid"}')
    signature = calendar_oauth._base64url(
        hmac.new(b"calendar-secret", body.encode("ascii"), hashlib.sha256).digest()
    )
    state = f"{body}.{signature}"

    with pytest.raises(GoogleCalendarOAuthError, match="state payload is invalid"):
        validate_google_calendar_oauth_state(
            settings=settings(),
            state=state,
            cookie_state=state,
            now=NOW,
        )


def test_google_calendar_oauth_requires_complete_config() -> None:
    missing = settings().model_copy(update={"google_calendar_oauth_client_id": None})

    with pytest.raises(GoogleCalendarOAuthError, match="not configured"):
        build_google_calendar_oauth_start(settings=missing, staff_id=STAFF_ID, now=NOW)

    blank_secret = settings().model_copy(
        update={"google_calendar_oauth_client_secret": SecretStr("   ")}
    )
    with pytest.raises(GoogleCalendarOAuthError, match="secret is invalid"):
        build_google_calendar_oauth_start(settings=blank_secret, staff_id=STAFF_ID, now=NOW)


def test_exchange_google_calendar_code_posts_authorization_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[urllib.request.Request] = []

    def urlopen(request: urllib.request.Request, timeout: int) -> _Response:
        requests.append(request)
        assert timeout == 10
        return _Response(
            {
                "access_token": "access-token",
                "scope": f"{GOOGLE_CALENDAR_EVENTS_READONLY_SCOPE} profile",
            }
        )

    monkeypatch.setattr(
        "golden_rose.application.google_calendar_oauth.urllib.request.urlopen", urlopen
    )

    token = exchange_google_calendar_code(settings=settings(), code="authorization-code")

    assert token.access_token == "access-token"
    assert token.granted_scopes == (GOOGLE_CALENDAR_EVENTS_READONLY_SCOPE, "profile")
    request = requests[0]
    assert request.full_url == GOOGLE_TOKEN_URL
    assert request.get_method() == "POST"
    assert request.data is not None
    body = cast(bytes, request.data).decode("utf-8")
    assert "code=authorization-code" in body
    assert "client_secret=calendar-secret" in body


def test_exchange_google_calendar_code_rejects_invalid_token_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "golden_rose.application.google_calendar_oauth.urllib.request.urlopen",
        lambda request, timeout: _Response({"access_token": "   "}),
    )

    with pytest.raises(GoogleCalendarOAuthError, match="token response is invalid"):
        exchange_google_calendar_code(settings=settings(), code="authorization-code")


def test_exchange_google_calendar_code_rejects_non_object_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "golden_rose.application.google_calendar_oauth.urllib.request.urlopen",
        lambda request, timeout: _Response(["not", "an", "object"]),
    )

    with pytest.raises(GoogleCalendarOAuthError, match="response is invalid"):
        exchange_google_calendar_code(settings=settings(), code="authorization-code")


def test_exchange_google_calendar_code_wraps_google_request_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def urlopen(request: urllib.request.Request, timeout: int) -> _Response:
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(
        "golden_rose.application.google_calendar_oauth.urllib.request.urlopen", urlopen
    )

    with pytest.raises(GoogleCalendarOAuthError, match="request failed"):
        exchange_google_calendar_code(settings=settings(), code="authorization-code")


def test_fetch_google_calendar_events_parses_bounded_safe_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[urllib.request.Request] = []

    def urlopen(request: urllib.request.Request, timeout: int) -> _Response:
        requests.append(request)
        return _Response(
            {
                "items": [
                    {
                        "id": "event-1",
                        "updated": "2026-10-11T20:59:00Z",
                        "summary": "Morning shift",
                        "start": {
                            "dateTime": "2026-10-12T09:00:00-04:00",
                            "timeZone": "America/New_York",
                        },
                        "end": {
                            "dateTime": "2026-10-12T13:00:00-04:00",
                            "timeZone": "America/New_York",
                        },
                        "location": "123 Private St",
                    },
                    {
                        "iCalUID": "event-2",
                        "start": {"date": "2026-10-13"},
                        "end": {"date": "2026-10-14"},
                    },
                    {"id": "cancelled", "status": "cancelled"},
                    {"id": "missing-end", "start": {"date": "2026-10-15"}},
                    {
                        "id": "backwards",
                        "start": {"date": "2026-10-15"},
                        "end": {"date": "2026-10-15"},
                    },
                    "not-an-event",
                ]
            }
        )

    monkeypatch.setattr(
        "golden_rose.application.google_calendar_oauth.urllib.request.urlopen", urlopen
    )

    events = fetch_google_calendar_events(access_token="access-token", now=NOW, window_days=14)

    assert len(events) == 2
    assert events[0].provider_event_uid == "event-1"
    assert events[0].event_title == "Morning shift"
    assert events[0].location_review == GOOGLE_CALENDAR_LOCATION_REVIEW
    assert events[0].provider_event_updated_at == datetime(2026, 10, 11, 20, 59, tzinfo=UTC)
    assert events[1].provider_event_uid == "event-2"
    assert events[1].event_title == "Untitled Google Calendar event"
    assert events[1].starts_at == datetime(2026, 10, 13, tzinfo=UTC)
    assert events[1].provider_event_updated_at == NOW
    request = requests[0]
    assert request.full_url.startswith(f"{GOOGLE_EVENTS_URL}?")
    assert request.headers["Authorization"] == "Bearer access-token"
    assert "maxResults=50" in request.full_url


def test_fetch_google_calendar_events_rejects_invalid_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "golden_rose.application.google_calendar_oauth.urllib.request.urlopen",
        lambda request, timeout: _Response({"items": "not-a-list"}),
    )

    with pytest.raises(GoogleCalendarOAuthError, match="events response is invalid"):
        fetch_google_calendar_events(access_token="access-token", now=NOW, window_days=14)


def test_fetch_google_calendar_events_skips_unparseable_items(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "golden_rose.application.google_calendar_oauth.urllib.request.urlopen",
        lambda request, timeout: _Response(
            {
                "items": [
                    {
                        "id": "   ",
                        "iCalUID": "",
                        "start": {"date": "2026-10-12"},
                        "end": {"date": "2026-10-13"},
                    },
                    {
                        "id": "invalid-datetime",
                        "start": {"dateTime": "not-a-date"},
                        "end": {"dateTime": "2026-10-13T10:00:00Z"},
                    },
                    {
                        "id": "invalid-date",
                        "start": {"date": "not-a-date"},
                        "end": {"date": "2026-10-13"},
                    },
                    {
                        "id": "missing-start-values",
                        "start": {"timeZone": "America/New_York"},
                        "end": {"date": "2026-10-13"},
                    },
                    {
                        "id": "naive-updated",
                        "updated": "2026-10-11T21:30:00",
                        "summary": "Naive timestamp",
                        "start": {"date": "2026-10-13"},
                        "end": {"date": "2026-10-14"},
                    },
                ]
            }
        ),
    )

    events = fetch_google_calendar_events(access_token="access-token", now=NOW, window_days=14)

    assert len(events) == 1
    assert events[0].provider_event_uid == "naive-updated"
    assert events[0].provider_event_updated_at == datetime(2026, 10, 11, 21, 30, tzinfo=UTC)


def test_fetch_google_calendar_events_rejects_non_json_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "golden_rose.application.google_calendar_oauth.urllib.request.urlopen",
        lambda request, timeout: _Response("not-json", content_type="text/html"),
    )

    with pytest.raises(GoogleCalendarOAuthError, match="response is not JSON"):
        fetch_google_calendar_events(access_token="access-token", now=NOW, window_days=14)


def test_google_calendar_location_notice_is_value_safe() -> None:
    assert "Calendar location attached" in GOOGLE_CALENDAR_LOCATION_REVIEW
    assert "http" not in GOOGLE_CALENDAR_LOCATION_REVIEW.lower()
