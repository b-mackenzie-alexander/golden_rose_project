from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import Engine, event, text

import golden_rose.api.staff.employers as employers_module
import golden_rose.application.search_employers as search_application_module
from golden_rose.api.dependencies import (
    get_clock,
    get_identifier_factory,
    get_staff_principal,
)
from golden_rose.application.errors import EmployerNotFoundError, SafePersistenceError
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


def test_search_returns_minimized_page_cursor_no_total_and_no_store(
    clean_tables,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    app = create_app()
    identifiers = FixedIdentifierFactory(
        UUID("71717171-7171-4171-8171-717171717171"),
        UUID("72727272-7272-4272-8272-727272727272"),
        UUID("73737373-7373-4373-8373-737373737373"),
        UUID("74747474-7474-4474-8474-747474747474"),
    )
    app.dependency_overrides[get_clock] = lambda: FixedClock(
        datetime(2026, 8, 5, 5, 0, 0, tzinfo=UTC)
    )
    app.dependency_overrides[get_identifier_factory] = lambda: identifiers
    with TestClient(app) as client:
        first_create = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "75757575-7575-4575-8575-757575757575"},
            json={
                "employer_type": "business",
                "display_name": "Rose Market Care",
            },
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 5, 6, 0, 0, tzinfo=UTC)
        )
        second_create = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "76767676-7676-4676-8676-767676767676"},
            json={
                "employer_type": "business",
                "display_name": "Golden Rose Staffing",
            },
        )

        assert first_create.status_code == 201
        assert second_create.status_code == 201

        response = client.post(
            "/api/staff/v1/employers/search",
            json={
                "display_name_query": "rose",
                "page_size": 1,
            },
        )

        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
        assert response.json()["items"] == [
            {
                "employer_id": "73737373-7373-4373-8373-737373737373",
                "employer_type": "business",
                "display_name": "Golden Rose Staffing",
                "lifecycle_status": "draft",
                "version": 1,
                "received_at": "2026-08-05T06:00:00Z",
            }
        ]
        assert isinstance(response.json()["next_cursor"], str)
        assert "total" not in response.json()


def test_authorized_invalid_search_inputs_return_nonreflective_no_store_422(
    clean_tables,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    with TestClient(create_app(), raise_server_exceptions=False) as client:
        response = client.post(
            "/api/staff/v1/employers/search",
            json={
                "display_name_query": "rose",
                "cursor": "bad-cursor",
            },
        )

        assert response.status_code == 422
        assert response.headers["Cache-Control"] == "no-store"
        assert response.json() == {
            "type": "https://golden-rose.local/problems/request-validation",
            "title": "Unprocessable Entity",
            "detail": "request validation failed",
            "status": 422,
        }


def test_search_failures_map_to_safe_redacted_503_and_500(
    clean_tables,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    def raise_safe_persistence_error(**_: object):
        raise SafePersistenceError("persistence operation failed")

    monkeypatch.setattr(
        employers_module,
        "search_employers",
        raise_safe_persistence_error,
    )

    def raise_unexpected_error(**_: object):
        raise RuntimeError("boom with secret-like text")

    with TestClient(create_app(), raise_server_exceptions=False) as client:
        unavailable_response = client.post(
            "/api/staff/v1/employers/search",
            json={"display_name_query": "rose"},
        )

        monkeypatch.setattr(
            employers_module,
            "search_employers",
            raise_unexpected_error,
        )
        unexpected_response = client.post(
            "/api/staff/v1/employers/search",
            json={"display_name_query": "rose"},
        )

        assert unavailable_response.status_code == 503
        assert unavailable_response.headers["Cache-Control"] == "no-store"
        assert unavailable_response.json() == {
            "type": "https://golden-rose.local/problems/service-unavailable",
            "title": "Service Unavailable",
            "detail": "service unavailable",
            "status": 503,
        }
        assert unexpected_response.status_code == 500
        assert unexpected_response.headers["Cache-Control"] == "no-store"
        assert unexpected_response.json() == {
            "type": "https://golden-rose.local/problems/internal-error",
            "title": "Internal Server Error",
            "detail": "internal server error",
            "status": 500,
        }


def test_get_existing_returns_exact_detail_with_no_store(
    clean_tables,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    app = create_app()
    app.dependency_overrides[get_clock] = lambda: FixedClock(
        datetime(2026, 8, 5, 7, 15, 0, tzinfo=UTC)
    )
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        UUID("81818181-8181-4181-8181-818181818181"),
        UUID("82828282-8282-4282-8282-828282828282"),
    )
    with TestClient(app) as client:
        create_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "83838383-8383-4383-8383-838383838383"},
            json={
                "employer_type": "household",
                "display_name": "Golden Detail Household",
            },
        )

        assert create_response.status_code == 201

        response = client.get("/api/staff/v1/employers/81818181-8181-4181-8181-818181818181")

        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
        assert response.json() == {
            "employer_id": "81818181-8181-4181-8181-818181818181",
            "employer_type": "household",
            "display_name": "Golden Detail Household",
            "lifecycle_status": "draft",
            "source_channel": "staff_entry",
            "version": 1,
            "received_at": "2026-08-05T07:15:00Z",
            "created_at": "2026-08-05T07:15:00Z",
        }


def test_get_absent_returns_nonreflective_no_store_404(
    clean_tables,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    def raise_not_found(**_: object):
        raise EmployerNotFoundError("employer not found")

    monkeypatch.setattr(
        employers_module,
        "get_employer",
        raise_not_found,
    )
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        response = client.get("/api/staff/v1/employers/91919191-9191-4191-8191-919191919191")

        assert response.status_code == 404
        assert response.headers["Cache-Control"] == "no-store"
        assert response.json() == {
            "type": "https://golden-rose.local/problems/employer-not-found",
            "title": "Not Found",
            "detail": "employer not found",
            "status": 404,
        }


def test_denied_get_runs_no_sql_and_headers_cannot_elevate(
    clean_tables,
    monkeypatch,
    engine: Engine,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    sql_statements: list[str] = []

    def record_sql(
        conn,
        cursor,
        statement: str,
        parameters,
        context,
        executemany,
    ) -> None:
        sql_statements.append(statement)

    event.listen(engine, "before_cursor_execute", record_sql)
    try:
        app = create_app()
        app.dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
            actor_id=UUID("92929292-9292-4292-8292-929292929292"),
            role_name="synthetic_staff",
            permissions=frozenset(),
        )
        with TestClient(app) as client:
            response = client.get(
                "/api/staff/v1/employers/93939393-9393-4393-8393-939393939393",
                headers={
                    "X-Actor-Id": "11111111-1111-4111-8111-111111111111",
                    "X-Role-Name": "platform_administrator",
                    "X-Permissions": "employer:read",
                },
            )
    finally:
        event.remove(engine, "before_cursor_execute", record_sql)

    assert response.status_code == 403
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json() == {
        "type": "https://golden-rose.local/problems/forbidden",
        "title": "Forbidden",
        "detail": "forbidden",
        "status": 403,
    }
    assert sql_statements == []


def test_detail_validation_and_failures_map_to_safe_no_store_problems(
    clean_tables,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    def raise_safe_persistence_error(**_: object):
        raise SafePersistenceError("persistence operation failed")

    monkeypatch.setattr(
        employers_module,
        "get_employer",
        raise_safe_persistence_error,
    )
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        invalid_uuid_response = client.get("/api/staff/v1/employers/not-a-uuid")
        unavailable_response = client.get(
            "/api/staff/v1/employers/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        )

        assert invalid_uuid_response.status_code == 422
        assert invalid_uuid_response.headers["Cache-Control"] == "no-store"
        assert invalid_uuid_response.json() == {
            "type": "https://golden-rose.local/problems/request-validation",
            "title": "Unprocessable Entity",
            "detail": "request validation failed",
            "status": 422,
        }
        assert unavailable_response.status_code == 503
        assert unavailable_response.headers["Cache-Control"] == "no-store"
        assert unavailable_response.json() == {
            "type": "https://golden-rose.local/problems/service-unavailable",
            "title": "Service Unavailable",
            "detail": "service unavailable",
            "status": 503,
        }


def test_search_filters_and_cursor_round_trip_over_http(
    clean_tables,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    app = create_app()
    identifiers = FixedIdentifierFactory(
        UUID("a1a1a1a1-a1a1-41a1-81a1-a1a1a1a1a1a1"),
        UUID("b1b1b1b1-b1b1-41b1-81b1-b1b1b1b1b1b1"),
        UUID("a2a2a2a2-a2a2-42a2-82a2-a2a2a2a2a2a2"),
        UUID("b2b2b2b2-b2b2-42b2-82b2-b2b2b2b2b2b2"),
        UUID("a3a3a3a3-a3a3-43a3-83a3-a3a3a3a3a3a3"),
        UUID("b3b3b3b3-b3b3-43b3-83b3-b3b3b3b3b3b3"),
    )
    app.dependency_overrides[get_identifier_factory] = lambda: identifiers
    with TestClient(app) as client:
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 5, 8, 0, 0, tzinfo=UTC)
        )
        newest_create = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "10101010-1010-4010-8010-101010101010"},
            json={
                "employer_type": "business",
                "display_name": "Golden Rose Staffing",
            },
        )

        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 5, 7, 0, 0, tzinfo=UTC)
        )
        middle_create = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "20202020-2020-4020-8020-202020202020"},
            json={
                "employer_type": "business",
                "display_name": "Rose Market Care",
            },
        )

        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 5, 6, 0, 0, tzinfo=UTC)
        )
        filtered_out_create = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "30303030-3030-4030-8030-303030303030"},
            json={
                "employer_type": "household",
                "display_name": "Rose Family Household",
            },
        )

        assert newest_create.status_code == 201
        assert middle_create.status_code == 201
        assert filtered_out_create.status_code == 201

        first_response = client.post(
            "/api/staff/v1/employers/search",
            json={
                "display_name_query": "rose",
                "employer_type": "business",
                "page_size": 1,
            },
        )

        assert first_response.status_code == 200
        assert first_response.headers["Cache-Control"] == "no-store"
        assert first_response.json() == {
            "items": [
                {
                    "employer_id": "a1a1a1a1-a1a1-41a1-81a1-a1a1a1a1a1a1",
                    "employer_type": "business",
                    "display_name": "Golden Rose Staffing",
                    "lifecycle_status": "draft",
                    "version": 1,
                    "received_at": "2026-08-05T08:00:00Z",
                }
            ],
            "next_cursor": first_response.json()["next_cursor"],
        }
        assert isinstance(first_response.json()["next_cursor"], str)

        second_response = client.post(
            "/api/staff/v1/employers/search",
            json={
                "display_name_query": "rose",
                "employer_type": "business",
                "page_size": 1,
                "cursor": first_response.json()["next_cursor"],
            },
        )

        assert second_response.status_code == 200
        assert second_response.headers["Cache-Control"] == "no-store"
        assert second_response.json() == {
            "items": [
                {
                    "employer_id": "a2a2a2a2-a2a2-42a2-82a2-a2a2a2a2a2a2",
                    "employer_type": "business",
                    "display_name": "Rose Market Care",
                    "lifecycle_status": "draft",
                    "version": 1,
                    "received_at": "2026-08-05T07:00:00Z",
                }
            ],
            "next_cursor": None,
        }


def test_denied_search_precedes_cursor_and_sql_and_headers_cannot_elevate(
    clean_tables,
    monkeypatch,
    engine: Engine,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    sql_statements: list[str] = []
    decode_calls = 0

    def record_sql(
        conn,
        cursor,
        statement: str,
        parameters,
        context,
        executemany,
    ) -> None:
        sql_statements.append(statement)

    def record_decode(*args, **kwargs):
        nonlocal decode_calls
        decode_calls += 1
        raise AssertionError("decode_search_cursor should not run for denied search")

    event.listen(engine, "before_cursor_execute", record_sql)
    monkeypatch.setattr(
        search_application_module,
        "decode_search_cursor",
        record_decode,
    )
    try:
        app = create_app()
        app.dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
            actor_id=UUID("94949494-9494-4494-8494-949494949494"),
            role_name="synthetic_staff",
            permissions=frozenset(),
        )
        with TestClient(app) as client:
            response = client.post(
                "/api/staff/v1/employers/search",
                headers={
                    "X-Actor-Id": "11111111-1111-4111-8111-111111111111",
                    "X-Role-Name": "platform_administrator",
                    "X-Permissions": "employer:read",
                },
                json={
                    "display_name_query": "rose",
                    "page_size": 1,
                    "cursor": "bad-cursor",
                },
            )
    finally:
        event.remove(engine, "before_cursor_execute", record_sql)

    assert response.status_code == 403
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json() == {
        "type": "https://golden-rose.local/problems/forbidden",
        "title": "Forbidden",
        "detail": "forbidden",
        "status": 403,
    }
    assert decode_calls == 0
    assert sql_statements == []


def test_detail_and_search_leave_authoritative_row_counts_unchanged(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    app = create_app()
    identifiers = FixedIdentifierFactory(
        UUID("c1c1c1c1-c1c1-41c1-81c1-c1c1c1c1c1c1"),
        UUID("d1d1d1d1-d1d1-41d1-81d1-d1d1d1d1d1d1"),
        UUID("c2c2c2c2-c2c2-42c2-82c2-c2c2c2c2c2c2"),
        UUID("d2d2d2d2-d2d2-42d2-82d2-d2d2d2d2d2d2"),
    )
    app.dependency_overrides[get_identifier_factory] = lambda: identifiers
    with TestClient(app) as client:
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 5, 9, 0, 0, tzinfo=UTC)
        )
        first_create = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "40404040-4040-4040-8040-404040404040"},
            json={
                "employer_type": "business",
                "display_name": "Count Stable Rose One",
            },
        )

        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 5, 8, 0, 0, tzinfo=UTC)
        )
        second_create = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "50505050-5050-4050-8050-505050505050"},
            json={
                "employer_type": "business",
                "display_name": "Count Stable Rose Two",
            },
        )

        assert first_create.status_code == 201
        assert second_create.status_code == 201

        baseline_employer_count = session.execute(
            text("SELECT COUNT(*) FROM employers")
        ).scalar_one()
        baseline_command_receipt_count = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        baseline_audit_event_count = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()

        detail_response = client.get("/api/staff/v1/employers/c1c1c1c1-c1c1-41c1-81c1-c1c1c1c1c1c1")
        search_response = client.post(
            "/api/staff/v1/employers/search",
            json={
                "display_name_query": "rose",
                "page_size": 1,
            },
        )

        assert detail_response.status_code == 200
        assert search_response.status_code == 200

        final_employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
        final_command_receipt_count = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        final_audit_event_count = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()

        assert final_employer_count == baseline_employer_count
        assert final_command_receipt_count == baseline_command_receipt_count
        assert final_audit_event_count == baseline_audit_event_count


def test_openapi_exposes_only_approved_staff_employer_routes() -> None:
    with TestClient(create_app()) as client:
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


def test_search_logs_do_not_include_body_cursor_filter_sql_url_actor_or_exception(
    clean_tables,
    monkeypatch,
    caplog,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    body_marker = "body-marker-rose"
    cursor_marker = "cursor-marker-rose"
    filter_marker = "filter-marker-rose"
    sql_marker = "sql-marker-rose"
    url_marker = "url-marker-rose"
    actor_marker = "actor-marker-rose"
    exception_marker = "exception-marker-rose"

    def raise_unexpected_error(**_: object):
        raise RuntimeError(
            f"{filter_marker} {sql_marker} {url_marker} {actor_marker} {exception_marker}"
        )

    monkeypatch.setattr(
        employers_module,
        "search_employers",
        raise_unexpected_error,
    )
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        response = client.post(
            "/api/staff/v1/employers/search",
            headers={"X-Actor-Id": actor_marker},
            json={
                "display_name_query": body_marker,
                "page_size": 1,
                "cursor": cursor_marker,
            },
        )

        assert response.status_code == 500
        assert response.headers["Cache-Control"] == "no-store"
        assert response.json() == {
            "type": "https://golden-rose.local/problems/internal-error",
            "title": "Internal Server Error",
            "detail": "internal server error",
            "status": 500,
        }
        assert body_marker not in caplog.text
        assert cursor_marker not in caplog.text
        assert filter_marker not in caplog.text
        assert sql_marker not in caplog.text
        assert url_marker not in caplog.text
        assert actor_marker not in caplog.text
        assert exception_marker not in caplog.text
