import base64
import hashlib
import hmac
import json
import secrets
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from pydantic import SecretStr

from golden_rose.application.calendar_imports import (
    GOOGLE_CALENDAR_EVENTS_READONLY_SCOPE,
    GoogleCalendarEventImport,
)
from golden_rose.config import Settings

GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"  # nosec B105
GOOGLE_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
GOOGLE_CALENDAR_OAUTH_STATE_TTL_SECONDS = 600
GOOGLE_CALENDAR_IMPORT_LIMIT = 50
GOOGLE_CALENDAR_LOCATION_REVIEW = "Google Calendar location attached; review source before copying."


@dataclass(frozen=True, slots=True)
class GoogleCalendarOAuthState:
    staff_id: UUID
    nonce: str
    issued_at: int


@dataclass(frozen=True, slots=True)
class GoogleCalendarOAuthStart:
    authorization_url: str
    state: str


@dataclass(frozen=True, slots=True)
class GoogleCalendarToken:
    access_token: str
    granted_scopes: tuple[str, ...]


class GoogleCalendarOAuthError(RuntimeError):
    pass


def build_google_calendar_oauth_start(
    *,
    settings: Settings,
    staff_id: UUID,
    now: datetime,
) -> GoogleCalendarOAuthStart:
    config = _require_google_calendar_oauth_config(settings)
    state = _encode_state(
        GoogleCalendarOAuthState(
            staff_id=staff_id,
            nonce=secrets.token_urlsafe(24),
            issued_at=int(now.timestamp()),
        ),
        secret=config.client_secret,
    )
    query = urllib.parse.urlencode(
        {
            "client_id": config.client_id,
            "redirect_uri": config.redirect_uri,
            "response_type": "code",
            "scope": GOOGLE_CALENDAR_EVENTS_READONLY_SCOPE,
            "state": state,
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",
        }
    )
    return GoogleCalendarOAuthStart(
        authorization_url=f"{GOOGLE_AUTHORIZATION_URL}?{query}",
        state=state,
    )


def validate_google_calendar_oauth_state(
    *,
    settings: Settings,
    state: str | None,
    cookie_state: str | None,
    now: datetime,
) -> GoogleCalendarOAuthState:
    config = _require_google_calendar_oauth_config(settings)
    if state is None or cookie_state is None or not hmac.compare_digest(state, cookie_state):
        raise GoogleCalendarOAuthError("Google Calendar OAuth state is invalid")
    decoded = _decode_state(state, secret=config.client_secret)
    age_seconds = int(now.timestamp()) - decoded.issued_at
    if age_seconds < 0 or age_seconds > GOOGLE_CALENDAR_OAUTH_STATE_TTL_SECONDS:
        raise GoogleCalendarOAuthError("Google Calendar OAuth state expired")
    return decoded


def exchange_google_calendar_code(
    *,
    settings: Settings,
    code: str,
) -> GoogleCalendarToken:
    config = _require_google_calendar_oauth_config(settings)
    body = urllib.parse.urlencode(
        {
            "code": code,
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "redirect_uri": config.redirect_uri,
            "grant_type": "authorization_code",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        GOOGLE_TOKEN_URL,
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    payload = _read_json(request)
    access_token = payload.get("access_token")
    scope_value = payload.get("scope")
    if not isinstance(access_token, str) or access_token.strip() == "":
        raise GoogleCalendarOAuthError("Google Calendar OAuth token response is invalid")
    scopes = (
        tuple(str(scope) for scope in scope_value.split())
        if isinstance(scope_value, str) and scope_value.strip() != ""
        else (GOOGLE_CALENDAR_EVENTS_READONLY_SCOPE,)
    )
    return GoogleCalendarToken(access_token=access_token, granted_scopes=scopes)


def fetch_google_calendar_events(
    *,
    access_token: str,
    now: datetime,
    window_days: int,
) -> tuple[GoogleCalendarEventImport, ...]:
    time_min = _google_timestamp(now)
    time_max = _google_timestamp(now + timedelta(days=window_days))
    query = urllib.parse.urlencode(
        {
            "singleEvents": "true",
            "orderBy": "startTime",
            "timeMin": time_min,
            "timeMax": time_max,
            "maxResults": str(GOOGLE_CALENDAR_IMPORT_LIMIT),
        }
    )
    request = urllib.request.Request(
        f"{GOOGLE_EVENTS_URL}?{query}",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
    )
    payload = _read_json(request)
    items = payload.get("items")
    if not isinstance(items, list):
        raise GoogleCalendarOAuthError("Google Calendar events response is invalid")
    events: list[GoogleCalendarEventImport] = []
    for item in items:
        parsed = _parse_google_calendar_event(item, now=now)
        if parsed is not None:
            events.append(parsed)
    return tuple(events)


@dataclass(frozen=True, slots=True)
class _GoogleCalendarOAuthConfig:
    client_id: str
    client_secret: str
    redirect_uri: str


def _require_google_calendar_oauth_config(settings: Settings) -> _GoogleCalendarOAuthConfig:
    if (
        settings.google_calendar_oauth_client_id is None
        or settings.google_calendar_oauth_client_secret is None
        or settings.google_calendar_oauth_redirect_uri is None
    ):
        raise GoogleCalendarOAuthError("Google Calendar OAuth is not configured")
    return _GoogleCalendarOAuthConfig(
        client_id=settings.google_calendar_oauth_client_id,
        client_secret=_secret_value(settings.google_calendar_oauth_client_secret),
        redirect_uri=settings.google_calendar_oauth_redirect_uri,
    )


def _secret_value(value: SecretStr) -> str:
    secret = value.get_secret_value().strip()
    if len(secret) == 0:
        raise GoogleCalendarOAuthError("Google Calendar OAuth secret is invalid")
    return secret


def _encode_state(state: GoogleCalendarOAuthState, *, secret: str) -> str:
    payload = json.dumps(
        {
            "staff_id": str(state.staff_id),
            "nonce": state.nonce,
            "iat": state.issued_at,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    body = _base64url(payload)
    signature = _base64url(
        hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    )
    return f"{body}.{signature}"


def _decode_state(value: str, *, secret: str) -> GoogleCalendarOAuthState:
    try:
        body, signature = value.split(".", 1)
    except ValueError as exc:
        raise GoogleCalendarOAuthError("Google Calendar OAuth state is invalid") from exc
    expected = _base64url(
        hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    )
    if not hmac.compare_digest(signature, expected):
        raise GoogleCalendarOAuthError("Google Calendar OAuth state signature is invalid")
    try:
        payload = json.loads(_base64url_decode(body))
        return GoogleCalendarOAuthState(
            staff_id=UUID(str(payload["staff_id"])),
            nonce=str(payload["nonce"]),
            issued_at=int(payload["iat"]),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise GoogleCalendarOAuthError("Google Calendar OAuth state payload is invalid") from exc


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _base64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _read_json(request: urllib.request.Request) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=10) as response:  # nosec B310
            content_type = response.headers.get("Content-Type", "")
            if "json" not in content_type:
                raise GoogleCalendarOAuthError("Google Calendar response is not JSON")
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise GoogleCalendarOAuthError("Google Calendar request failed") from exc
    if not isinstance(payload, dict):
        raise GoogleCalendarOAuthError("Google Calendar response is invalid")
    return payload


def _parse_google_calendar_event(
    value: Any,
    *,
    now: datetime,
) -> GoogleCalendarEventImport | None:
    if not isinstance(value, dict) or value.get("status") == "cancelled":
        return None
    provider_uid = value.get("id") or value.get("iCalUID")
    if not isinstance(provider_uid, str) or provider_uid.strip() == "":
        return None
    start_value = _parse_event_time(value.get("start"))
    end_value = _parse_event_time(value.get("end"))
    if start_value is None or end_value is None or end_value[0] <= start_value[0]:
        return None
    updated_at = _parse_rfc3339(value.get("updated")) or now
    title = value.get("summary") if isinstance(value.get("summary"), str) else None
    location = value.get("location")
    return GoogleCalendarEventImport(
        provider_event_uid=provider_uid,
        provider_event_updated_at=updated_at,
        event_title=(title or "Untitled Google Calendar event")[:200],
        starts_at=start_value[0],
        ends_at=end_value[0],
        time_zone=start_value[1],
        location_review=(
            GOOGLE_CALENDAR_LOCATION_REVIEW
            if isinstance(location, str) and location.strip() != ""
            else None
        ),
    )


def _parse_event_time(value: Any) -> tuple[datetime, str] | None:
    if not isinstance(value, dict):
        return None
    date_time_value = value.get("dateTime")
    if isinstance(date_time_value, str):
        parsed = _parse_rfc3339(date_time_value)
        if parsed is None:
            return None
        time_zone = value.get("timeZone")
        return parsed, str(time_zone).strip()[:64] if isinstance(
            time_zone, str
        ) and time_zone.strip() else "UTC"
    date_value = value.get("date")
    if isinstance(date_value, str):
        try:
            parsed_date = date.fromisoformat(date_value)
        except ValueError:
            return None
        time_zone = value.get("timeZone")
        return (
            datetime(parsed_date.year, parsed_date.month, parsed_date.day, tzinfo=UTC),
            str(time_zone).strip()[:64]
            if isinstance(time_zone, str) and time_zone.strip()
            else "UTC",
        )
    return None


def _parse_rfc3339(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _google_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
