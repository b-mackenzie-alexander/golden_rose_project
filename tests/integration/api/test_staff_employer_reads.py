import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import Engine, event, text

import golden_rose.api.staff.employers as employers_module
import golden_rose.application.contact_cursor as contact_cursor_application_module
import golden_rose.application.create_employer_contact as create_employer_contact_application_module
import golden_rose.application.get_employer_contact as get_employer_contact_application_module
import golden_rose.application.query_employer_contacts as query_employer_contacts_application_module
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


def test_post_staff_employer_contact_returns_exact_201_contract_and_replay_headers(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("81818181-aaaa-4aaa-8aaa-818181818181")
    create_employer_event_id = UUID("82828282-bbbb-4bbb-8bbb-828282828282")
    employer_contact_id = UUID("83838383-cccc-4ccc-8ccc-838383838383")
    create_contact_event_id = UUID("84848484-dddd-4ddd-8ddd-848484848484")

    app = create_app()
    with TestClient(app) as client:
        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            employer_id,
            create_employer_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 20, 0, 0, tzinfo=UTC)
        )
        create_employer_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "85858585-eeee-4eee-8eee-858585858585"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Employer Contact Parent",
            },
        )

        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            employer_contact_id,
            create_contact_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 20, 5, 0, tzinfo=UTC)
        )
        first_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts",
            headers={"Idempotency-Key": "86868686-ffff-4fff-8fff-868686868686"},
            json={"full_name": "Synthetic Contact API 001"},
        )
        replay_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts",
            headers={"Idempotency-Key": "86868686-ffff-4fff-8fff-868686868686"},
            json={"full_name": "Synthetic Contact API 001"},
        )

    assert create_employer_response.status_code == 201

    expected_body = {
        "employer_contact_id": str(employer_contact_id),
        "employer_id": str(employer_id),
        "full_name": "Synthetic Contact API 001",
        "version": 1,
        "created_at": "2026-08-12T20:05:00Z",
        "updated_at": "2026-08-12T20:05:00Z",
    }

    assert first_response.status_code == 201
    assert replay_response.status_code == 201
    assert first_response.headers["Content-Type"] == "application/json"
    assert replay_response.headers["Content-Type"] == "application/json"
    assert first_response.headers["Cache-Control"] == "no-store"
    assert replay_response.headers["Cache-Control"] == "no-store"
    assert first_response.headers["Idempotency-Result-Version"] == "1"
    assert replay_response.headers["Idempotency-Result-Version"] == "1"
    assert "Idempotency-Replayed" not in first_response.headers
    assert replay_response.headers["Idempotency-Replayed"] == "true"
    assert first_response.json() == expected_body
    assert replay_response.json() == expected_body
    assert "location" not in {key.lower() for key in first_response.headers}
    assert "location" not in {key.lower() for key in replay_response.headers}

    assert session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one() == 1
    assert session.execute(text("SELECT COUNT(*) FROM employer_contacts")).scalar_one() == 1
    assert session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one() == 2
    assert session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one() == 2

    stored_contact = (
        session.execute(
            text(
                """
            SELECT employer_contact_id, employer_id, full_name, version, created_at, updated_at
            FROM employer_contacts
            """
            )
        )
        .mappings()
        .one()
    )
    assert stored_contact == {
        "employer_contact_id": employer_contact_id,
        "employer_id": employer_id,
        "full_name": "Synthetic Contact API 001",
        "version": 1,
        "created_at": datetime(2026, 8, 12, 20, 5, 0, tzinfo=UTC),
        "updated_at": datetime(2026, 8, 12, 20, 5, 0, tzinfo=UTC),
    }


def test_post_staff_employer_contact_failure_matrix_is_exact_no_store_value_safe_and_write_free(
    clean_tables,
    monkeypatch,
    session,
    engine: Engine,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("89898989-aaaa-4aaa-8aaa-898989898989")
    create_employer_event_id = UUID("8a8a8a8a-bbbb-4bbb-8bbb-8a8a8a8a8a8a")
    employer_contact_id = UUID("9a9a9a9a-e0e0-40e0-80e0-9a9a9a9a9a9a")
    create_contact_event_id = UUID("9b9b9b9b-f0f0-40f0-80f0-9b9b9b9b9b9b")
    original_create_employer_contact = (
        create_employer_contact_application_module.create_employer_contact
    )

    app = create_app()
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        employer_id,
        create_employer_event_id,
    )
    app.dependency_overrides[get_clock] = lambda: FixedClock(
        datetime(2026, 8, 12, 20, 10, 0, tzinfo=UTC)
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        create_employer_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "8b8b8b8b-cccc-4ccc-8ccc-8b8b8b8b8b8b"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Employer Contact Failure Parent",
            },
        )

        assert create_employer_response.status_code == 201

        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            employer_contact_id,
            create_contact_event_id,
        )

        cases = [
            (
                "invalid-idempotency-key",
                f"/api/staff/v1/employers/{employer_id}/contacts",
                {"Idempotency-Key": "not-a-uuid"},
                {"full_name": "Synthetic Contact Failure Value"},
                400,
                {
                    "type": "https://golden-rose.local/problems/invalid-idempotency-key",
                    "title": "Bad Request",
                    "detail": "invalid idempotency key",
                    "status": 400,
                },
            ),
            (
                "missing-parent",
                "/api/staff/v1/employers/8c8c8c8c-dddd-4ddd-8ddd-8c8c8c8c8c8c/contacts",
                {"Idempotency-Key": "8d8d8d8d-eeee-4eee-8eee-8d8d8d8d8d8d"},
                {"full_name": "Synthetic Contact Missing Parent Value"},
                404,
                {
                    "type": "https://golden-rose.local/problems/employer-not-found",
                    "title": "Not Found",
                    "detail": "employer not found",
                    "status": 404,
                },
            ),
            (
                "invalid-name",
                f"/api/staff/v1/employers/{employer_id}/contacts",
                {"Idempotency-Key": "8e8e8e8e-ffff-4fff-8fff-8e8e8e8e8e8e"},
                {"full_name": "Synthetic Contact\nControl Value"},
                422,
                {
                    "type": "https://golden-rose.local/problems/request-validation",
                    "title": "Unprocessable Entity",
                    "detail": "request validation failed",
                    "status": 422,
                },
            ),
            (
                "request-validation",
                f"/api/staff/v1/employers/{employer_id}/contacts",
                {"Idempotency-Key": "8f8f8f8f-abab-4bab-8bab-8f8f8f8f8f8f"},
                {"created_by": "forbidden"},
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
            assert response.headers["Content-Type"] == "application/json"
            assert response.headers["Cache-Control"] == "no-store"
            assert response.json() == expected_problem
            assert "Idempotency-Result-Version" not in response.headers
            assert "Idempotency-Replayed" not in response.headers
            assert "Synthetic Contact" not in response.text
            assert str(employer_id) not in response.text
            assert "8c8c8c8c" not in response.text
            assert "created_by" not in response.text
            assert "not-a-uuid" not in response.text

        assert session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one() == 1
        assert session.execute(text("SELECT COUNT(*) FROM employer_contacts")).scalar_one() == 0
        assert session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one() == 1
        assert session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one() == 1

        conflict_key = "90909090-bcbc-4cbc-8cbc-909090909090"
        first_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts",
            headers={"Idempotency-Key": conflict_key},
            json={"full_name": "Synthetic Contact Conflict Seed"},
        )
        employer_contact_count_before_conflict = session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one()
        receipt_count_before_conflict = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count_before_conflict = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()
        conflict_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts",
            headers={"Idempotency-Key": conflict_key},
            json={"full_name": "Synthetic Contact Conflict Value"},
        )
        employer_contact_count_after_conflict = session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one()
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
        assert "Synthetic Contact Conflict" not in conflict_response.text
        assert "Idempotency-Result-Version" not in conflict_response.headers
        assert "Idempotency-Replayed" not in conflict_response.headers
        assert employer_contact_count_before_conflict == 1
        assert receipt_count_before_conflict == 2
        assert audit_event_count_before_conflict == 2
        assert employer_contact_count_after_conflict == employer_contact_count_before_conflict
        assert receipt_count_after_conflict == receipt_count_before_conflict
        assert audit_event_count_after_conflict == audit_event_count_before_conflict

    def raise_safe_persistence_error(**_: object):
        raise SafePersistenceError(
            "persistence operation failed Synthetic Contact Persistence Value"
        )

    monkeypatch.setattr(
        employers_module,
        "create_employer_contact",
        raise_safe_persistence_error,
    )
    with TestClient(create_app(), raise_server_exceptions=False) as unavailable_client:
        unavailable_response = unavailable_client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts",
            headers={"Idempotency-Key": "91919191-cdcd-4dcd-8dcd-919191919191"},
            json={"full_name": "Synthetic Contact Persistence Value"},
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
    assert "Synthetic Contact Persistence" not in unavailable_response.text
    assert "Idempotency-Result-Version" not in unavailable_response.headers
    assert "Idempotency-Replayed" not in unavailable_response.headers

    def raise_unexpected_error(**_: object):
        raise RuntimeError("Synthetic Contact Unexpected Value")

    monkeypatch.setattr(
        employers_module,
        "create_employer_contact",
        raise_unexpected_error,
    )
    with TestClient(create_app(), raise_server_exceptions=False) as error_client:
        unexpected_response = error_client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts",
            headers={"Idempotency-Key": "92929292-dede-4ede-8ede-929292929292"},
            json={"full_name": "Synthetic Contact Unexpected Value"},
        )

    assert unexpected_response.status_code == 500
    assert unexpected_response.headers["Content-Type"] == "application/json"
    assert unexpected_response.headers["Cache-Control"] == "no-store"
    assert unexpected_response.json() == {
        "type": "https://golden-rose.local/problems/internal-error",
        "title": "Internal Server Error",
        "detail": "internal server error",
        "status": 500,
    }
    assert "Synthetic Contact Unexpected" not in unexpected_response.text
    assert "Idempotency-Result-Version" not in unexpected_response.headers
    assert "Idempotency-Replayed" not in unexpected_response.headers

    monkeypatch.setattr(
        employers_module,
        "create_employer_contact",
        original_create_employer_contact,
    )

    sql_statements: list[str] = []
    validation_calls = 0

    def record_sql(
        conn,
        cursor,
        statement: str,
        parameters,
        context,
        executemany,
    ) -> None:
        sql_statements.append(statement)

    def record_validation(value: str) -> str:
        nonlocal validation_calls
        validation_calls += 1
        raise AssertionError("validate_contact_full_name should not run for denied contact create")

    event.listen(engine, "before_cursor_execute", record_sql)
    monkeypatch.setattr(
        create_employer_contact_application_module,
        "validate_contact_full_name",
        record_validation,
    )
    try:
        denied_app = create_app()
        denied_app.dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
            actor_id=UUID("93939393-efef-4fef-8fef-939393939393"),
            role_name="synthetic_staff_without_contact_create",
            permissions=frozenset(),
        )
        with TestClient(denied_app, raise_server_exceptions=False) as denied_client:
            denied_invalid_name_response = denied_client.post(
                f"/api/staff/v1/employers/{employer_id}/contacts",
                headers={"Idempotency-Key": "94949494-f0f0-40f0-80f0-949494949494"},
                json={"full_name": "Denied\nSensitive Contact"},
            )
            denied_missing_header_response = denied_client.post(
                f"/api/staff/v1/employers/{employer_id}/contacts",
                json={"full_name": "Denied Missing Header Contact"},
            )
            denied_bad_path_response = denied_client.post(
                "/api/staff/v1/employers/not-a-uuid/contacts",
                headers={"Idempotency-Key": "95959595-a0a0-40a0-80a0-959595959595"},
                json={"full_name": "Denied Bad Path Contact"},
            )
            denied_wrong_body_type_response = denied_client.post(
                f"/api/staff/v1/employers/{employer_id}/contacts",
                headers={"Idempotency-Key": "96969696-b0b0-40b0-80b0-969696969696"},
                json={"full_name": {"nested": "value"}},
            )
            denied_missing_field_response = denied_client.post(
                f"/api/staff/v1/employers/{employer_id}/contacts",
                headers={"Idempotency-Key": "97979797-c0c0-40c0-80c0-979797979797"},
                json={},
            )
            denied_extra_field_response = denied_client.post(
                f"/api/staff/v1/employers/{employer_id}/contacts",
                headers={"Idempotency-Key": "98989898-d0d0-40d0-80d0-989898989898"},
                json={
                    "full_name": "Denied Extra Field Contact",
                    "created_by": "forbidden",
                },
            )
    finally:
        event.remove(engine, "before_cursor_execute", record_sql)

    denied_cases = [
        (
            denied_invalid_name_response,
            403,
            {
                "type": "https://golden-rose.local/problems/forbidden",
                "title": "Forbidden",
                "detail": "forbidden",
                "status": 403,
            },
        ),
        (
            denied_missing_header_response,
            400,
            {
                "type": "https://golden-rose.local/problems/invalid-idempotency-key",
                "title": "Bad Request",
                "detail": "invalid idempotency key",
                "status": 400,
            },
        ),
        (
            denied_bad_path_response,
            422,
            {
                "type": "https://golden-rose.local/problems/request-validation",
                "title": "Unprocessable Entity",
                "detail": "request validation failed",
                "status": 422,
            },
        ),
        (
            denied_wrong_body_type_response,
            422,
            {
                "type": "https://golden-rose.local/problems/request-validation",
                "title": "Unprocessable Entity",
                "detail": "request validation failed",
                "status": 422,
            },
        ),
        (
            denied_missing_field_response,
            422,
            {
                "type": "https://golden-rose.local/problems/request-validation",
                "title": "Unprocessable Entity",
                "detail": "request validation failed",
                "status": 422,
            },
        ),
        (
            denied_extra_field_response,
            422,
            {
                "type": "https://golden-rose.local/problems/request-validation",
                "title": "Unprocessable Entity",
                "detail": "request validation failed",
                "status": 422,
            },
        ),
    ]

    for response, status_code, expected_problem in denied_cases:
        assert response.status_code == status_code
        assert response.headers["Content-Type"] == "application/json"
        assert response.headers["Cache-Control"] == "no-store"
        assert response.json() == expected_problem
        assert "Idempotency-Result-Version" not in response.headers
        assert "Idempotency-Replayed" not in response.headers
        assert "Denied" not in response.text
        assert str(employer_id) not in response.text
        assert "created_by" not in response.text
        assert "not-a-uuid" not in response.text

    assert validation_calls == 0
    assert sql_statements == []
    assert session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one() == 1
    assert session.execute(text("SELECT COUNT(*) FROM employer_contacts")).scalar_one() == 1
    assert session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one() == 2
    assert session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one() == 2


def test_post_staff_employer_contact_query_returns_exact_200_bounded_page_without_count_or_writes(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("a0a0a0a0-aaaa-4aaa-8aaa-a0a0a0a0a0a0")
    create_employer_event_id = UUID("a1a1a1a1-bbbb-4bbb-8bbb-a1a1a1a1a1a1")
    first_contact_id = UUID("a2a2a2a2-cccc-4ccc-8ccc-a2a2a2a2a2a2")
    first_contact_event_id = UUID("a3a3a3a3-dddd-4ddd-8ddd-a3a3a3a3a3a3")
    second_contact_id = UUID("a4a4a4a4-eeee-4eee-8eee-a4a4a4a4a4a4")
    second_contact_event_id = UUID("a5a5a5a5-ffff-4fff-8fff-a5a5a5a5a5a5")

    app = create_app()
    with TestClient(app) as client:
        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            employer_id,
            create_employer_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 20, 20, 0, tzinfo=UTC)
        )
        create_employer_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "a6a6a6a6-abab-4bab-8bab-a6a6a6a6a6a6"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Employer Contact Query Parent",
            },
        )

        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            first_contact_id,
            first_contact_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 20, 21, 0, tzinfo=UTC)
        )
        first_contact_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts",
            headers={"Idempotency-Key": "a7a7a7a7-bcbc-4cbc-8cbc-a7a7a7a7a7a7"},
            json={"full_name": "Synthetic Contact Query Older"},
        )

        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            second_contact_id,
            second_contact_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 20, 22, 0, tzinfo=UTC)
        )
        second_contact_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts",
            headers={"Idempotency-Key": "a8a8a8a8-cdcd-4dcd-8dcd-a8a8a8a8a8a8"},
            json={"full_name": "Synthetic Contact Query Newer"},
        )

        employer_count_before_query = session.execute(
            text("SELECT COUNT(*) FROM employers")
        ).scalar_one()
        employer_contact_count_before_query = session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one()
        command_receipt_count_before_query = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count_before_query = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()

        response = client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts/query",
            json={"page_size": 1},
        )

        employer_count_after_query = session.execute(
            text("SELECT COUNT(*) FROM employers")
        ).scalar_one()
        employer_contact_count_after_query = session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one()
        command_receipt_count_after_query = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count_after_query = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()

    assert create_employer_response.status_code == 201
    assert first_contact_response.status_code == 201
    assert second_contact_response.status_code == 201
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers["Cache-Control"] == "no-store"
    assert "Idempotency-Result-Version" not in response.headers
    assert "Idempotency-Replayed" not in response.headers
    assert response.json() == {
        "items": [
            {
                "employer_contact_id": str(second_contact_id),
                "employer_id": str(employer_id),
                "full_name": "Synthetic Contact Query Newer",
                "version": 1,
                "created_at": "2026-08-12T20:22:00Z",
                "updated_at": "2026-08-12T20:22:00Z",
            }
        ],
        "next_cursor": response.json()["next_cursor"],
    }
    assert isinstance(response.json()["next_cursor"], str)
    assert "total" not in response.json()
    assert employer_count_before_query == 1
    assert employer_contact_count_before_query == 2
    assert command_receipt_count_before_query == 3
    assert audit_event_count_before_query == 3
    assert employer_count_after_query == employer_count_before_query
    assert employer_contact_count_after_query == employer_contact_count_before_query
    assert command_receipt_count_after_query == command_receipt_count_before_query
    assert audit_event_count_after_query == audit_event_count_before_query


def test_post_staff_employer_contact_query_failure_matrix_is_exact_no_store_value_safe_and_write_free(  # noqa: E501
    clean_tables,
    monkeypatch,
    session,
    engine: Engine,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("b0b0b0b0-aaaa-4aaa-8aaa-b0b0b0b0b0b0")
    create_employer_event_id = UUID("b1b1b1b1-bbbb-4bbb-8bbb-b1b1b1b1b1b1")
    employer_contact_id = UUID("b2b2b2b2-cccc-4ccc-8ccc-b2b2b2b2b2b2")
    create_contact_event_id = UUID("b3b3b3b3-dddd-4ddd-8ddd-b3b3b3b3b3b3")
    original_query_employer_contacts = (
        query_employer_contacts_application_module.query_employer_contacts
    )

    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            employer_id,
            create_employer_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 20, 30, 0, tzinfo=UTC)
        )
        create_employer_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "b4b4b4b4-eeee-4eee-8eee-b4b4b4b4b4b4"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Employer Contact Query Failure Parent",
            },
        )

        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            employer_contact_id,
            create_contact_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 20, 31, 0, tzinfo=UTC)
        )
        create_contact_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts",
            headers={"Idempotency-Key": "b5b5b5b5-ffff-4fff-8fff-b5b5b5b5b5b5"},
            json={"full_name": "Synthetic Contact Query Failure Seed"},
        )

        cases = [
            (
                "transport-validation-page-size",
                f"/api/staff/v1/employers/{employer_id}/contacts/query",
                {"page_size": 0},
                422,
                {
                    "type": "https://golden-rose.local/problems/request-validation",
                    "title": "Unprocessable Entity",
                    "detail": "request validation failed",
                    "status": 422,
                },
            ),
            (
                "transport-validation-overlength-cursor",
                f"/api/staff/v1/employers/{employer_id}/contacts/query",
                {"page_size": 1, "cursor": "x" * 513},
                422,
                {
                    "type": "https://golden-rose.local/problems/request-validation",
                    "title": "Unprocessable Entity",
                    "detail": "request validation failed",
                    "status": 422,
                },
            ),
            (
                "invalid-cursor",
                f"/api/staff/v1/employers/{employer_id}/contacts/query",
                {"page_size": 1, "cursor": "bad-cursor"},
                422,
                {
                    "type": "https://golden-rose.local/problems/request-validation",
                    "title": "Unprocessable Entity",
                    "detail": "request validation failed",
                    "status": 422,
                },
            ),
            (
                "missing-parent",
                "/api/staff/v1/employers/b6b6b6b6-a0a0-40a0-80a0-b6b6b6b6b6b6/contacts/query",
                {"page_size": 1},
                404,
                {
                    "type": "https://golden-rose.local/problems/employer-not-found",
                    "title": "Not Found",
                    "detail": "employer not found",
                    "status": 404,
                },
            ),
        ]

        for label, path, body, status_code, expected_problem in cases:
            response = client.post(path, json=body)

            assert response.status_code == status_code, label
            assert response.headers["Content-Type"] == "application/json"
            assert response.headers["Cache-Control"] == "no-store"
            assert response.json() == expected_problem
            assert "Idempotency-Result-Version" not in response.headers
            assert "Idempotency-Replayed" not in response.headers
            assert "Synthetic Contact Query Failure" not in response.text
            assert str(employer_id) not in response.text
            assert "bad-cursor" not in response.text

        assert create_employer_response.status_code == 201
        assert create_contact_response.status_code == 201
        assert session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one() == 1
        assert session.execute(text("SELECT COUNT(*) FROM employer_contacts")).scalar_one() == 1
        assert session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one() == 2
        assert session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one() == 2

    def raise_safe_persistence_error(**_: object):
        raise SafePersistenceError(
            "persistence failed with Synthetic Contact Query Persistence Value"
        )

    monkeypatch.setattr(
        employers_module,
        "query_employer_contacts",
        raise_safe_persistence_error,
    )
    with TestClient(create_app(), raise_server_exceptions=False) as unavailable_client:
        unavailable_response = unavailable_client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts/query",
            json={"page_size": 1},
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
    assert "Synthetic Contact Query Persistence" not in unavailable_response.text
    assert "Idempotency-Result-Version" not in unavailable_response.headers
    assert "Idempotency-Replayed" not in unavailable_response.headers

    def raise_unexpected_error(**_: object):
        raise RuntimeError("Synthetic Contact Query Unexpected Value")

    monkeypatch.setattr(
        employers_module,
        "query_employer_contacts",
        raise_unexpected_error,
    )
    with TestClient(create_app(), raise_server_exceptions=False) as error_client:
        unexpected_response = error_client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts/query",
            json={"page_size": 1},
        )

    assert unexpected_response.status_code == 500
    assert unexpected_response.headers["Content-Type"] == "application/json"
    assert unexpected_response.headers["Cache-Control"] == "no-store"
    assert unexpected_response.json() == {
        "type": "https://golden-rose.local/problems/internal-error",
        "title": "Internal Server Error",
        "detail": "internal server error",
        "status": 500,
    }
    assert "Synthetic Contact Query Unexpected" not in unexpected_response.text
    assert "Idempotency-Result-Version" not in unexpected_response.headers
    assert "Idempotency-Replayed" not in unexpected_response.headers

    monkeypatch.setattr(
        employers_module,
        "query_employer_contacts",
        original_query_employer_contacts,
    )

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
        raise AssertionError("decode_contact_cursor should not run for denied contact query")

    cross_parent_cursor = contact_cursor_application_module.encode_contact_cursor(
        contact_cursor_application_module.ContactCursor(
            version=1,
            employer_id=UUID("b7b7b7b7-b0b0-40b0-80b0-b7b7b7b7b7b7"),
            page_size=1,
            after_created_at=datetime(2026, 8, 12, 20, 40, 0, tzinfo=UTC),
            after_employer_contact_id=UUID("b8b8b8b8-c0c0-40c0-80c0-b8b8b8b8b8b8"),
        )
    )

    event.listen(engine, "before_cursor_execute", record_sql)
    monkeypatch.setattr(
        query_employer_contacts_application_module,
        "decode_contact_cursor",
        record_decode,
    )
    try:
        denied_app = create_app()
        denied_app.dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
            actor_id=UUID("b9b9b9b9-d0d0-40d0-80d0-b9b9b9b9b9b9"),
            role_name="synthetic_staff_without_contact_query",
            permissions=frozenset(),
        )
        with TestClient(denied_app, raise_server_exceptions=False) as denied_client:
            denied_malformed_cursor_response = denied_client.post(
                f"/api/staff/v1/employers/{employer_id}/contacts/query",
                headers={
                    "X-Staff-Actor-Id": "11111111-1111-4111-8111-111111111111",
                    "X-Staff-Role": "platform_admin",
                    "X-Staff-Permissions": "employer:read,employer_contact:read",
                },
                json={"page_size": 1, "cursor": "bad-cursor"},
            )
            denied_cross_parent_cursor_response = denied_client.post(
                f"/api/staff/v1/employers/{employer_id}/contacts/query",
                json={"page_size": 1, "cursor": cross_parent_cursor},
            )
            denied_transport_validation_response = denied_client.post(
                f"/api/staff/v1/employers/{employer_id}/contacts/query",
                json={"page_size": 0},
            )
            denied_extra_field_response = denied_client.post(
                f"/api/staff/v1/employers/{employer_id}/contacts/query",
                json={"page_size": 1, "created_by": "forbidden"},
            )
    finally:
        event.remove(engine, "before_cursor_execute", record_sql)

    assert denied_malformed_cursor_response.status_code == 403
    assert denied_malformed_cursor_response.headers["Content-Type"] == "application/json"
    assert denied_malformed_cursor_response.headers["Cache-Control"] == "no-store"
    assert denied_malformed_cursor_response.json() == {
        "type": "https://golden-rose.local/problems/forbidden",
        "title": "Forbidden",
        "detail": "forbidden",
        "status": 403,
    }
    assert denied_cross_parent_cursor_response.status_code == 403
    assert denied_cross_parent_cursor_response.headers["Content-Type"] == "application/json"
    assert denied_cross_parent_cursor_response.headers["Cache-Control"] == "no-store"
    assert denied_cross_parent_cursor_response.json() == {
        "type": "https://golden-rose.local/problems/forbidden",
        "title": "Forbidden",
        "detail": "forbidden",
        "status": 403,
    }
    assert denied_transport_validation_response.status_code == 422
    assert denied_transport_validation_response.headers["Content-Type"] == "application/json"
    assert denied_transport_validation_response.headers["Cache-Control"] == "no-store"
    assert denied_transport_validation_response.json() == {
        "type": "https://golden-rose.local/problems/request-validation",
        "title": "Unprocessable Entity",
        "detail": "request validation failed",
        "status": 422,
    }
    assert denied_extra_field_response.status_code == 422
    assert denied_extra_field_response.headers["Content-Type"] == "application/json"
    assert denied_extra_field_response.headers["Cache-Control"] == "no-store"
    assert denied_extra_field_response.json() == {
        "type": "https://golden-rose.local/problems/request-validation",
        "title": "Unprocessable Entity",
        "detail": "request validation failed",
        "status": 422,
    }
    assert "Idempotency-Result-Version" not in denied_malformed_cursor_response.headers
    assert "Idempotency-Replayed" not in denied_malformed_cursor_response.headers
    assert "Idempotency-Result-Version" not in denied_cross_parent_cursor_response.headers
    assert "Idempotency-Replayed" not in denied_cross_parent_cursor_response.headers
    assert "Idempotency-Result-Version" not in denied_transport_validation_response.headers
    assert "Idempotency-Replayed" not in denied_transport_validation_response.headers
    assert "Idempotency-Result-Version" not in denied_extra_field_response.headers
    assert "Idempotency-Replayed" not in denied_extra_field_response.headers
    assert decode_calls == 0
    assert sql_statements == []
    assert session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one() == 1
    assert session.execute(text("SELECT COUNT(*) FROM employer_contacts")).scalar_one() == 1
    assert session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one() == 2
    assert session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one() == 2


def test_post_staff_employer_contact_query_cursor_is_parent_and_page_size_bound(
    clean_tables,
    monkeypatch,
    session,
    engine: Engine,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("c0c0c0c0-aaaa-4aaa-8aaa-c0c0c0c0c0c0")
    create_employer_event_id = UUID("c1c1c1c1-bbbb-4bbb-8bbb-c1c1c1c1c1c1")
    first_contact_id = UUID("c2c2c2c2-cccc-4ccc-8ccc-c2c2c2c2c2c2")
    first_contact_event_id = UUID("c3c3c3c3-dddd-4ddd-8ddd-c3c3c3c3c3c3")
    second_contact_id = UUID("c4c4c4c4-eeee-4eee-8eee-c4c4c4c4c4c4")
    second_contact_event_id = UUID("c5c5c5c5-ffff-4fff-8fff-c5c5c5c5c5c5")
    other_employer_id = UUID("c6c6c6c6-a0a0-40a0-80a0-c6c6c6c6c6c6")
    other_create_employer_event_id = UUID("c7c7c7c7-b0b0-40b0-80b0-c7c7c7c7c7c7")

    app = create_app()
    with TestClient(app) as client:
        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            employer_id,
            create_employer_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 20, 40, 0, tzinfo=UTC)
        )
        create_employer_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "c8c8c8c8-c1c1-41c1-81c1-c8c8c8c8c8c8"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Employer Contact Cursor Parent",
            },
        )

        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            other_employer_id,
            other_create_employer_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 20, 41, 0, tzinfo=UTC)
        )
        other_employer_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "c9c9c9c9-c2c2-42c2-82c2-c9c9c9c9c9c9"},
            json={
                "employer_type": "business",
                "display_name": "Synthetic Employer Contact Cursor Other Parent",
            },
        )

        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            first_contact_id,
            first_contact_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 20, 42, 0, tzinfo=UTC)
        )
        first_contact_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts",
            headers={"Idempotency-Key": "cacacaca-c3c3-43c3-83c3-cacacacacaca"},
            json={"full_name": "Synthetic Contact Cursor Older"},
        )

        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            second_contact_id,
            second_contact_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 20, 43, 0, tzinfo=UTC)
        )
        second_contact_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts",
            headers={"Idempotency-Key": "cbcbcbcb-c4c4-44c4-84c4-cbcbcbcbcbcb"},
            json={"full_name": "Synthetic Contact Cursor Newer"},
        )

        first_page_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts/query",
            json={"page_size": 1},
        )

        assert create_employer_response.status_code == 201
        assert other_employer_response.status_code == 201
        assert first_contact_response.status_code == 201
        assert second_contact_response.status_code == 201
        assert first_page_response.status_code == 200
        assert isinstance(first_page_response.json()["next_cursor"], str)

        baseline_counts = {
            "employers": session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one(),
            "employer_contacts": session.execute(
                text("SELECT COUNT(*) FROM employer_contacts")
            ).scalar_one(),
            "command_receipts": session.execute(
                text("SELECT COUNT(*) FROM command_receipts")
            ).scalar_one(),
            "audit_events": session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one(),
        }
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
            cross_parent_response = client.post(
                f"/api/staff/v1/employers/{other_employer_id}/contacts/query",
                json={"page_size": 1, "cursor": first_page_response.json()["next_cursor"]},
            )
            changed_page_size_response = client.post(
                f"/api/staff/v1/employers/{employer_id}/contacts/query",
                json={"page_size": 2, "cursor": first_page_response.json()["next_cursor"]},
            )
        finally:
            event.remove(engine, "before_cursor_execute", record_sql)

    expected_problem = {
        "type": "https://golden-rose.local/problems/request-validation",
        "title": "Unprocessable Entity",
        "detail": "request validation failed",
        "status": 422,
    }

    assert cross_parent_response.status_code == 422
    assert cross_parent_response.headers["Content-Type"] == "application/json"
    assert cross_parent_response.headers["Cache-Control"] == "no-store"
    assert cross_parent_response.json() == expected_problem
    assert changed_page_size_response.status_code == 422
    assert changed_page_size_response.headers["Content-Type"] == "application/json"
    assert changed_page_size_response.headers["Cache-Control"] == "no-store"
    assert changed_page_size_response.json() == expected_problem
    assert "Idempotency-Result-Version" not in cross_parent_response.headers
    assert "Idempotency-Replayed" not in cross_parent_response.headers
    assert "Idempotency-Result-Version" not in changed_page_size_response.headers
    assert "Idempotency-Replayed" not in changed_page_size_response.headers
    assert first_page_response.json()["next_cursor"] not in cross_parent_response.text
    assert first_page_response.json()["next_cursor"] not in changed_page_size_response.text
    assert str(employer_id) not in cross_parent_response.text
    assert str(other_employer_id) not in cross_parent_response.text
    assert str(employer_id) not in changed_page_size_response.text
    assert sql_statements == []
    assert {
        "employers": session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one(),
        "employer_contacts": session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one(),
        "command_receipts": session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one(),
        "audit_events": session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one(),
    } == baseline_counts


def test_get_staff_employer_contact_returns_exact_200_parent_scoped_contract_without_writes(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("d0d0d0d0-aaaa-4aaa-8aaa-d0d0d0d0d0d0")
    create_employer_event_id = UUID("d1d1d1d1-bbbb-4bbb-8bbb-d1d1d1d1d1d1")
    employer_contact_id = UUID("d2d2d2d2-cccc-4ccc-8ccc-d2d2d2d2d2d2")
    create_contact_event_id = UUID("d3d3d3d3-dddd-4ddd-8ddd-d3d3d3d3d3d3")

    app = create_app()
    with TestClient(app) as client:
        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            employer_id,
            create_employer_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 20, 50, 0, tzinfo=UTC)
        )
        create_employer_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "d4d4d4d4-eeee-4eee-8eee-d4d4d4d4d4d4"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Employer Contact Get Parent",
            },
        )

        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            employer_contact_id,
            create_contact_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 20, 51, 0, tzinfo=UTC)
        )
        create_contact_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts",
            headers={"Idempotency-Key": "d5d5d5d5-ffff-4fff-8fff-d5d5d5d5d5d5"},
            json={"full_name": "Synthetic Contact Get Detail"},
        )

        employer_count_before_get = session.execute(
            text("SELECT COUNT(*) FROM employers")
        ).scalar_one()
        employer_contact_count_before_get = session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one()
        command_receipt_count_before_get = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count_before_get = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()

        response = client.get(
            f"/api/staff/v1/employers/{employer_id}/contacts/{employer_contact_id}"
        )

        employer_count_after_get = session.execute(
            text("SELECT COUNT(*) FROM employers")
        ).scalar_one()
        employer_contact_count_after_get = session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one()
        command_receipt_count_after_get = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count_after_get = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()

    assert create_employer_response.status_code == 201
    assert create_contact_response.status_code == 201
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers["Cache-Control"] == "no-store"
    assert "Idempotency-Result-Version" not in response.headers
    assert "Idempotency-Replayed" not in response.headers
    assert response.json() == {
        "employer_contact_id": str(employer_contact_id),
        "employer_id": str(employer_id),
        "full_name": "Synthetic Contact Get Detail",
        "version": 1,
        "created_at": "2026-08-12T20:51:00Z",
        "updated_at": "2026-08-12T20:51:00Z",
    }
    assert employer_count_before_get == 1
    assert employer_contact_count_before_get == 1
    assert command_receipt_count_before_get == 2
    assert audit_event_count_before_get == 2
    assert employer_count_after_get == employer_count_before_get
    assert employer_contact_count_after_get == employer_contact_count_before_get
    assert command_receipt_count_after_get == command_receipt_count_before_get
    assert audit_event_count_after_get == audit_event_count_before_get


def test_get_staff_employer_contact_failure_matrix_is_exact_no_store_value_safe_and_write_free(
    clean_tables,
    monkeypatch,
    session,
    engine: Engine,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_id = UUID("e0e0e0e0-aaaa-4aaa-8aaa-e0e0e0e0e0e0")
    create_employer_event_id = UUID("e1e1e1e1-bbbb-4bbb-8bbb-e1e1e1e1e1e1")
    other_employer_id = UUID("e2e2e2e2-cccc-4ccc-8ccc-e2e2e2e2e2e2")
    other_create_employer_event_id = UUID("e3e3e3e3-dddd-4ddd-8ddd-e3e3e3e3e3e3")
    other_parent_contact_id = UUID("e4e4e4e4-eeee-4eee-8eee-e4e4e4e4e4e4")
    other_parent_contact_event_id = UUID("e5e5e5e5-ffff-4fff-8fff-e5e5e5e5e5e5")
    missing_contact_id = UUID("e6e6e6e6-a0a0-40a0-80a0-e6e6e6e6e6e6")
    original_get_employer_contact = get_employer_contact_application_module.get_employer_contact

    app = create_app()
    with TestClient(app) as client:
        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            employer_id,
            create_employer_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 21, 0, 0, tzinfo=UTC)
        )
        create_employer_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "e7e7e7e7-b1b1-41b1-81b1-e7e7e7e7e7e7"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Employer Contact Failure Primary Parent",
            },
        )

        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            other_employer_id,
            other_create_employer_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 21, 1, 0, tzinfo=UTC)
        )
        other_employer_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "e8e8e8e8-c2c2-42c2-82c2-e8e8e8e8e8e8"},
            json={
                "employer_type": "business",
                "display_name": "Synthetic Employer Contact Failure Other Parent",
            },
        )

        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            other_parent_contact_id,
            other_parent_contact_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 21, 2, 0, tzinfo=UTC)
        )
        create_other_parent_contact_response = client.post(
            f"/api/staff/v1/employers/{other_employer_id}/contacts",
            headers={"Idempotency-Key": "e9e9e9e9-d3d3-43d3-83d3-e9e9e9e9e9e9"},
            json={"full_name": "Synthetic Contact Failure Other Parent"},
        )

        assert create_employer_response.status_code == 201
        assert other_employer_response.status_code == 201
        assert create_other_parent_contact_response.status_code == 201

    baseline_counts = {
        "employers": session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one(),
        "employer_contacts": session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one(),
        "command_receipts": session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one(),
        "audit_events": session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one(),
    }

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
        with TestClient(create_app(), raise_server_exceptions=False) as client:
            invalid_uuid_response = client.get(
                f"/api/staff/v1/employers/{employer_id}/contacts/not-a-uuid"
            )

        denied_app = create_app()
        denied_app.dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
            actor_id=UUID("ebebebeb-e5e5-45e5-85e5-ebebebebebeb"),
            role_name="synthetic_staff_without_contact_read",
            permissions=frozenset(),
        )
        with TestClient(denied_app, raise_server_exceptions=False) as denied_client:
            denied_missing_response = denied_client.get(
                f"/api/staff/v1/employers/{employer_id}/contacts/{missing_contact_id}",
                headers={
                    "X-Staff-Actor-Id": "11111111-1111-4111-8111-111111111111",
                    "X-Staff-Role": "platform_admin",
                    "X-Staff-Permissions": "employer:read,employer_contact:read",
                },
            )
            denied_cross_parent_response = denied_client.get(
                f"/api/staff/v1/employers/{employer_id}/contacts/{other_parent_contact_id}"
            )
    finally:
        event.remove(engine, "before_cursor_execute", record_sql)

    with TestClient(create_app(), raise_server_exceptions=False) as not_found_client:
        missing_response = not_found_client.get(
            f"/api/staff/v1/employers/{employer_id}/contacts/{missing_contact_id}"
        )
        cross_parent_response = not_found_client.get(
            f"/api/staff/v1/employers/{employer_id}/contacts/{other_parent_contact_id}"
        )

    def raise_safe_persistence_error(**_: object):
        raise SafePersistenceError(
            "persistence failed with Synthetic Contact Detail Persistence Value"
        )

    monkeypatch.setattr(
        employers_module,
        "get_employer_contact",
        raise_safe_persistence_error,
    )
    with TestClient(create_app(), raise_server_exceptions=False) as unavailable_client:
        unavailable_response = unavailable_client.get(
            f"/api/staff/v1/employers/{employer_id}/contacts/{missing_contact_id}"
        )

    def raise_unexpected_error(**_: object):
        raise RuntimeError("Synthetic Contact Detail Unexpected Value")

    monkeypatch.setattr(
        employers_module,
        "get_employer_contact",
        raise_unexpected_error,
    )
    with TestClient(create_app(), raise_server_exceptions=False) as error_client:
        unexpected_response = error_client.get(
            f"/api/staff/v1/employers/{employer_id}/contacts/{missing_contact_id}"
        )

    monkeypatch.setattr(
        employers_module,
        "get_employer_contact",
        original_get_employer_contact,
    )

    expected_validation_problem = {
        "type": "https://golden-rose.local/problems/request-validation",
        "title": "Unprocessable Entity",
        "detail": "request validation failed",
        "status": 422,
    }
    expected_forbidden_problem = {
        "type": "https://golden-rose.local/problems/forbidden",
        "title": "Forbidden",
        "detail": "forbidden",
        "status": 403,
    }
    expected_not_found_problem = {
        "type": "https://golden-rose.local/problems/employer-contact-not-found",
        "title": "Not Found",
        "detail": "employer contact not found",
        "status": 404,
    }
    expected_unavailable_problem = {
        "type": "https://golden-rose.local/problems/service-unavailable",
        "title": "Service Unavailable",
        "detail": "service unavailable",
        "status": 503,
    }
    expected_internal_problem = {
        "type": "https://golden-rose.local/problems/internal-error",
        "title": "Internal Server Error",
        "detail": "internal server error",
        "status": 500,
    }

    cases = [
        ("invalid-uuid", invalid_uuid_response, 422, expected_validation_problem),
        ("denied-missing", denied_missing_response, 403, expected_forbidden_problem),
        (
            "denied-cross-parent",
            denied_cross_parent_response,
            403,
            expected_forbidden_problem,
        ),
        ("missing", missing_response, 404, expected_not_found_problem),
        ("cross-parent", cross_parent_response, 404, expected_not_found_problem),
        ("unavailable", unavailable_response, 503, expected_unavailable_problem),
        ("unexpected", unexpected_response, 500, expected_internal_problem),
    ]

    for label, response, status_code, expected_problem in cases:
        assert response.status_code == status_code, label
        assert response.headers["Content-Type"] == "application/json"
        assert response.headers["Cache-Control"] == "no-store"
        assert response.json() == expected_problem
        assert "Idempotency-Result-Version" not in response.headers
        assert "Idempotency-Replayed" not in response.headers
        assert "Synthetic Contact Failure Other Parent" not in response.text
        assert str(employer_id) not in response.text
        assert str(other_parent_contact_id) not in response.text
        assert str(missing_contact_id) not in response.text
        assert "not-a-uuid" not in response.text

    assert missing_response.content == cross_parent_response.content
    assert sql_statements == []
    assert {
        "employers": session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one(),
        "employer_contacts": session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one(),
        "command_receipts": session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one(),
        "audit_events": session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one(),
    } == baseline_counts


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


def test_existing_search_success_media_cache_body_headers_and_read_only_contract_remains_exact(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    app = create_app()
    identifiers = FixedIdentifierFactory(
        UUID("11111111-aaaa-4aaa-8aaa-111111111111"),
        UUID("22222222-bbbb-4bbb-8bbb-222222222222"),
        UUID("33333333-cccc-4ccc-8ccc-333333333333"),
        UUID("44444444-dddd-4ddd-8ddd-444444444444"),
    )
    app.dependency_overrides[get_identifier_factory] = lambda: identifiers
    with TestClient(app) as client:
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 11, 2, 40, 0, tzinfo=UTC)
        )
        first_create = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "45454545-aaaa-4aaa-8aaa-454545454545"},
            json={
                "employer_type": "business",
                "display_name": "Synthetic Search Alpha Rose",
            },
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 11, 2, 45, 0, tzinfo=UTC)
        )
        second_create = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "46464646-bbbb-4bbb-8bbb-464646464646"},
            json={
                "employer_type": "household",
                "display_name": "Synthetic Search Beta Rose",
            },
        )
        command_receipt_count_before_search = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count_before_search = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()

        response = client.post(
            "/api/staff/v1/employers/search",
            json={
                "display_name_query": "rose",
                "employer_type": "household",
                "page_size": 10,
            },
        )

        command_receipt_count = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

        assert first_create.status_code == 201
        assert second_create.status_code == 201
        assert first_create.headers["Idempotency-Result-Version"] == "1"
        assert second_create.headers["Idempotency-Result-Version"] == "1"
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/json"
        assert response.headers["Cache-Control"] == "no-store"
        assert "Idempotency-Result-Version" not in response.headers
        assert "Idempotency-Replayed" not in response.headers
        assert response.json() == {
            "items": [
                {
                    "employer_id": "33333333-cccc-4ccc-8ccc-333333333333",
                    "employer_type": "household",
                    "display_name": "Synthetic Search Beta Rose",
                    "lifecycle_status": "draft",
                    "version": 1,
                    "received_at": "2026-08-11T02:45:00Z",
                }
            ],
            "next_cursor": None,
        }
        assert "total" not in response.json()
        assert command_receipt_count_before_search == 2
        assert audit_event_count_before_search == 2
        assert command_receipt_count == command_receipt_count_before_search
        assert audit_event_count == audit_event_count_before_search


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


def test_existing_search_failure_matrix_media_cache_body_headers_and_read_only_contract_remains_exact(  # noqa: E501
    clean_tables,
    monkeypatch,
    session,
    engine: Engine,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    with TestClient(create_app(), raise_server_exceptions=False) as client:
        validation_response = client.post(
            "/api/staff/v1/employers/search",
            json={
                "display_name_query": "rose",
                "cursor": "Synthetic Search Bad Cursor Value",
            },
        )

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
        denied_app = create_app()
        denied_app.dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
            actor_id=UUID("47474747-aaaa-4aaa-8aaa-474747474747"),
            role_name="synthetic_staff_without_read",
            permissions=frozenset(),
        )
        with TestClient(denied_app, raise_server_exceptions=False) as denied_client:
            denied_response = denied_client.post(
                "/api/staff/v1/employers/search",
                headers={
                    "X-Staff-Actor-Id": "48484848-bbbb-4bbb-8bbb-484848484848",
                    "X-Staff-Role": "platform_admin",
                    "X-Staff-Permissions": "employer:read",
                },
                json={"display_name_query": "rose"},
            )
    finally:
        event.remove(engine, "before_cursor_execute", record_sql)

    def raise_safe_persistence_error(**_: object):
        raise SafePersistenceError("persistence failed with Synthetic Search Persistence Value")

    monkeypatch.setattr(employers_module, "search_employers", raise_safe_persistence_error)
    with TestClient(create_app(), raise_server_exceptions=False) as unavailable_client:
        unavailable_response = unavailable_client.post(
            "/api/staff/v1/employers/search",
            json={"display_name_query": "Synthetic Search Persistence Value"},
        )

    def raise_unexpected_error(**_: object):
        raise RuntimeError("unexpected Synthetic Search Internal Value")

    monkeypatch.setattr(employers_module, "search_employers", raise_unexpected_error)
    with TestClient(create_app(), raise_server_exceptions=False) as error_client:
        unexpected_response = error_client.post(
            "/api/staff/v1/employers/search",
            json={"display_name_query": "Synthetic Search Internal Value"},
        )

    cases = [
        (
            "validation",
            validation_response,
            422,
            {
                "type": "https://golden-rose.local/problems/request-validation",
                "title": "Unprocessable Entity",
                "detail": "request validation failed",
                "status": 422,
            },
        ),
        (
            "denied",
            denied_response,
            403,
            {
                "type": "https://golden-rose.local/problems/forbidden",
                "title": "Forbidden",
                "detail": "forbidden",
                "status": 403,
            },
        ),
        (
            "unavailable",
            unavailable_response,
            503,
            {
                "type": "https://golden-rose.local/problems/service-unavailable",
                "title": "Service Unavailable",
                "detail": "service unavailable",
                "status": 503,
            },
        ),
        (
            "unexpected",
            unexpected_response,
            500,
            {
                "type": "https://golden-rose.local/problems/internal-error",
                "title": "Internal Server Error",
                "detail": "internal server error",
                "status": 500,
            },
        ),
    ]

    for label, response, status_code, expected_problem in cases:
        assert response.status_code == status_code, label
        assert response.headers["Content-Type"] == "application/json"
        assert response.headers["Cache-Control"] == "no-store"
        assert response.json() == expected_problem
        assert "Idempotency-Result-Version" not in response.headers
        assert "Idempotency-Replayed" not in response.headers
        assert "Synthetic Search" not in response.text

    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert sql_statements == []
    assert employer_count == 0
    assert command_receipt_count == 0
    assert audit_event_count == 0


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
            "updated_at": "2026-08-05T07:15:00Z",
        }


def test_existing_detail_success_media_cache_body_headers_and_read_only_contract_remains_exact(
    clean_tables,
    monkeypatch,
    session,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    app = create_app()
    app.dependency_overrides[get_clock] = lambda: FixedClock(
        datetime(2026, 8, 11, 2, 50, 0, tzinfo=UTC)
    )
    app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
        UUID("49494949-aaaa-4aaa-8aaa-494949494949"),
        UUID("50505050-bbbb-4bbb-8bbb-505050505050"),
    )
    with TestClient(app) as client:
        create_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "51515151-cccc-4ccc-8ccc-515151515151"},
            json={
                "employer_type": "business",
                "display_name": "Synthetic Detail Compatibility",
            },
        )
        command_receipt_count_before_detail = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count_before_detail = session.execute(
            text("SELECT COUNT(*) FROM audit_events")
        ).scalar_one()

        response = client.get("/api/staff/v1/employers/49494949-aaaa-4aaa-8aaa-494949494949")

        command_receipt_count = session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one()
        audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

        assert create_response.status_code == 201
        assert create_response.headers["Idempotency-Result-Version"] == "1"
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/json"
        assert response.headers["Cache-Control"] == "no-store"
        assert "Idempotency-Result-Version" not in response.headers
        assert "Idempotency-Replayed" not in response.headers
        assert response.json() == {
            "employer_id": "49494949-aaaa-4aaa-8aaa-494949494949",
            "employer_type": "business",
            "display_name": "Synthetic Detail Compatibility",
            "lifecycle_status": "draft",
            "source_channel": "staff_entry",
            "version": 1,
            "received_at": "2026-08-11T02:50:00Z",
            "created_at": "2026-08-11T02:50:00Z",
            "updated_at": "2026-08-11T02:50:00Z",
        }
        assert command_receipt_count_before_detail == 1
        assert audit_event_count_before_detail == 1
        assert command_receipt_count == command_receipt_count_before_detail
        assert audit_event_count == audit_event_count_before_detail


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


def test_existing_detail_failure_matrix_media_cache_body_headers_and_read_only_contract_remains_exact(  # noqa: E501
    clean_tables,
    monkeypatch,
    session,
    engine: Engine,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    with TestClient(create_app(), raise_server_exceptions=False) as client:
        invalid_uuid_response = client.get("/api/staff/v1/employers/not-a-uuid")

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
        denied_app = create_app()
        denied_app.dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
            actor_id=UUID("53535353-bbbb-4bbb-8bbb-535353535353"),
            role_name="synthetic_staff_without_read",
            permissions=frozenset(),
        )
        with TestClient(denied_app, raise_server_exceptions=False) as denied_client:
            denied_response = denied_client.get(
                "/api/staff/v1/employers/54545454-cccc-4ccc-8ccc-545454545454",
                headers={
                    "X-Staff-Actor-Id": "55555555-dddd-4ddd-8ddd-555555555555",
                    "X-Staff-Role": "platform_admin",
                    "X-Staff-Permissions": "employer:read",
                },
            )
    finally:
        event.remove(engine, "before_cursor_execute", record_sql)

    def raise_not_found(**_: object):
        raise EmployerNotFoundError("employer not found Synthetic Detail Missing Value")

    monkeypatch.setattr(employers_module, "get_employer", raise_not_found)
    with TestClient(create_app(), raise_server_exceptions=False) as not_found_client:
        not_found_response = not_found_client.get(
            "/api/staff/v1/employers/52525252-aaaa-4aaa-8aaa-525252525252"
        )

    def raise_safe_persistence_error(**_: object):
        raise SafePersistenceError("persistence failed with Synthetic Detail Persistence Value")

    monkeypatch.setattr(employers_module, "get_employer", raise_safe_persistence_error)
    with TestClient(create_app(), raise_server_exceptions=False) as unavailable_client:
        unavailable_response = unavailable_client.get(
            "/api/staff/v1/employers/56565656-eeee-4eee-8eee-565656565656"
        )

    def raise_unexpected_error(**_: object):
        raise RuntimeError("unexpected Synthetic Detail Internal Value")

    monkeypatch.setattr(employers_module, "get_employer", raise_unexpected_error)
    with TestClient(create_app(), raise_server_exceptions=False) as error_client:
        unexpected_response = error_client.get(
            "/api/staff/v1/employers/57575757-ffff-4fff-8fff-575757575757"
        )

    cases = [
        (
            "validation",
            invalid_uuid_response,
            422,
            {
                "type": "https://golden-rose.local/problems/request-validation",
                "title": "Unprocessable Entity",
                "detail": "request validation failed",
                "status": 422,
            },
        ),
        (
            "not-found",
            not_found_response,
            404,
            {
                "type": "https://golden-rose.local/problems/employer-not-found",
                "title": "Not Found",
                "detail": "employer not found",
                "status": 404,
            },
        ),
        (
            "denied",
            denied_response,
            403,
            {
                "type": "https://golden-rose.local/problems/forbidden",
                "title": "Forbidden",
                "detail": "forbidden",
                "status": 403,
            },
        ),
        (
            "unavailable",
            unavailable_response,
            503,
            {
                "type": "https://golden-rose.local/problems/service-unavailable",
                "title": "Service Unavailable",
                "detail": "service unavailable",
                "status": 503,
            },
        ),
        (
            "unexpected",
            unexpected_response,
            500,
            {
                "type": "https://golden-rose.local/problems/internal-error",
                "title": "Internal Server Error",
                "detail": "internal server error",
                "status": 500,
            },
        ),
    ]

    for label, response, status_code, expected_problem in cases:
        assert response.status_code == status_code, label
        assert response.headers["Content-Type"] == "application/json"
        assert response.headers["Cache-Control"] == "no-store"
        assert response.json() == expected_problem
        assert "Idempotency-Result-Version" not in response.headers
        assert "Idempotency-Replayed" not in response.headers
        assert "Synthetic Detail" not in response.text
        assert "not-a-uuid" not in response.text
        assert "52525252" not in response.text

    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert sql_statements == []
    assert employer_count == 0
    assert command_receipt_count == 0
    assert audit_event_count == 0


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
            "/api/staff/v1/staff-accounts",
            "/api/staff/v1/staff-accounts/{staff_id}",
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
            "/api/staff/v1/employers/{employer_id}",
            "/api/staff/v1/employers/{employer_id}/revisions",
            "/api/staff/v1/employers/{employer_id}/contacts",
            "/api/staff/v1/employers/{employer_id}/contacts/query",
            "/api/staff/v1/employers/{employer_id}/contacts/{employer_contact_id}",
        }
        assert set(paths["/health"]) == {"get"}
        assert set(paths["/readiness"]) == {"get"}
        assert set(paths["/api/staff/v1/session"]) == {"get"}
        assert set(paths["/api/staff/v1/staff-accounts"]) == {"get", "post"}
        assert set(paths["/api/staff/v1/staff-accounts/{staff_id}"]) == {"get"}
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


def test_staff_employer_contact_openapi_exposes_only_approved_contract() -> None:
    with TestClient(create_app()) as client:
        openapi = client.get("/openapi.json")

        assert openapi.status_code == 200
        document = openapi.json()
        paths = document["paths"]
        schemas = document["components"]["schemas"]

        contact_paths = {path: paths[path] for path in paths if "/contacts" in path}
        assert set(contact_paths) == {
            "/api/staff/v1/employers/{employer_id}/contacts/{contact_id}/details/corrections",
            "/api/staff/v1/employers/{employer_id}/contacts/{contact_id}/details/address/corrections",
            "/api/staff/v1/employers/{employer_id}/contacts/{contact_id}/details",
            "/api/staff/v1/employers/{employer_id}/contacts/{contact_id}/details/address",
            "/api/staff/v1/employers/{employer_id}/contacts",
            "/api/staff/v1/employers/{employer_id}/contacts/query",
            "/api/staff/v1/employers/{employer_id}/contacts/{employer_contact_id}",
        }

        create_path = paths["/api/staff/v1/employers/{employer_id}/contacts"]
        assert set(create_path) == {"post"}
        create_operation = create_path["post"]
        assert create_operation["tags"] == ["staff-employers"]
        assert create_operation["parameters"] == [
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
        assert create_operation["requestBody"] == {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/EmployerContactCreateRequest"}
                }
            },
        }
        assert create_operation["responses"] == {
            "201": {
                "description": "Successful Response",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/EmployerContactResponse"}
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

        query_path = paths["/api/staff/v1/employers/{employer_id}/contacts/query"]
        assert set(query_path) == {"post"}
        query_operation = query_path["post"]
        assert query_operation["tags"] == ["staff-employers"]
        assert query_operation["parameters"] == [
            {
                "name": "employer_id",
                "in": "path",
                "required": True,
                "schema": {"type": "string", "format": "uuid", "title": "Employer Id"},
            }
        ]
        assert query_operation["requestBody"] == {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/EmployerContactQueryRequest"}
                }
            },
        }
        assert query_operation["responses"] == {
            "200": {
                "description": "Successful Response",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/EmployerContactQueryPageResponse"}
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

        get_path = paths["/api/staff/v1/employers/{employer_id}/contacts/{employer_contact_id}"]
        assert set(get_path) == {"get"}
        get_operation = get_path["get"]
        assert get_operation["tags"] == ["staff-employers"]
        assert get_operation["parameters"] == [
            {
                "name": "employer_id",
                "in": "path",
                "required": True,
                "schema": {"type": "string", "format": "uuid", "title": "Employer Id"},
            },
            {
                "name": "employer_contact_id",
                "in": "path",
                "required": True,
                "schema": {"type": "string", "format": "uuid", "title": "Employer Contact Id"},
            },
        ]
        assert get_operation["responses"] == {
            "200": {
                "description": "Successful Response",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/EmployerContactResponse"}
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

        assert schemas["EmployerContactCreateRequest"] == {
            "title": "EmployerContactCreateRequest",
            "type": "object",
            "additionalProperties": False,
            "required": ["full_name"],
            "properties": {
                "full_name": {
                    "title": "Full Name",
                    "type": "string",
                }
            },
        }
        assert schemas["EmployerContactQueryRequest"] == {
            "title": "EmployerContactQueryRequest",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "page_size": {
                    "default": 25,
                    "maximum": 50.0,
                    "minimum": 1.0,
                    "title": "Page Size",
                    "type": "integer",
                },
                "cursor": {
                    "anyOf": [
                        {
                            "maxLength": 512,
                            "type": "string",
                        },
                        {
                            "type": "null",
                        },
                    ],
                    "title": "Cursor",
                },
            },
        }
        assert schemas["EmployerContactResponse"] == {
            "title": "EmployerContactResponse",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "employer_contact_id",
                "employer_id",
                "full_name",
                "version",
                "created_at",
                "updated_at",
            ],
            "properties": {
                "employer_contact_id": {
                    "type": "string",
                    "format": "uuid",
                    "title": "Employer Contact Id",
                },
                "employer_id": {
                    "type": "string",
                    "format": "uuid",
                    "title": "Employer Id",
                },
                "full_name": {
                    "title": "Full Name",
                    "type": "string",
                },
                "version": {
                    "title": "Version",
                    "type": "integer",
                },
                "created_at": {
                    "type": "string",
                    "format": "date-time",
                    "title": "Created At",
                },
                "updated_at": {
                    "type": "string",
                    "format": "date-time",
                    "title": "Updated At",
                },
            },
        }
        assert schemas["EmployerContactSummaryResponse"] == {
            "title": "EmployerContactSummaryResponse",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "employer_contact_id",
                "employer_id",
                "full_name",
                "version",
                "created_at",
                "updated_at",
            ],
            "properties": {
                "employer_contact_id": {
                    "type": "string",
                    "format": "uuid",
                    "title": "Employer Contact Id",
                },
                "employer_id": {
                    "type": "string",
                    "format": "uuid",
                    "title": "Employer Id",
                },
                "full_name": {
                    "title": "Full Name",
                    "type": "string",
                },
                "version": {
                    "title": "Version",
                    "type": "integer",
                },
                "created_at": {
                    "type": "string",
                    "format": "date-time",
                    "title": "Created At",
                },
                "updated_at": {
                    "type": "string",
                    "format": "date-time",
                    "title": "Updated At",
                },
            },
        }
        assert schemas["EmployerContactQueryPageResponse"] == {
            "title": "EmployerContactQueryPageResponse",
            "type": "object",
            "additionalProperties": False,
            "required": ["items", "next_cursor"],
            "properties": {
                "items": {
                    "title": "Items",
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/EmployerContactSummaryResponse"},
                },
                "next_cursor": {
                    "anyOf": [
                        {
                            "type": "string",
                        },
                        {
                            "type": "null",
                        },
                    ],
                    "title": "Next Cursor",
                },
            },
        }


def test_staff_employer_contact_unmatched_and_method_not_allowed_routes_do_not_execute_or_reflect_contact_markers(  # noqa: E501
    clean_tables,
    monkeypatch,
    session,
    engine: Engine,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    employer_marker = "f1f1f1f1-1111-4111-8111-f1f1f1f1f1f1"
    contact_marker = "f2f2f2f2-2222-4222-8222-f2f2f2f2f2f2"
    unmatched_marker = "unmatched-contact-marker"

    baseline_counts = {
        "employers": session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one(),
        "employer_contacts": session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one(),
        "command_receipts": session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one(),
        "audit_events": session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one(),
    }
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
        with TestClient(create_app(), raise_server_exceptions=False) as client:
            create_method_not_allowed_response = client.put(
                f"/api/staff/v1/employers/{employer_marker}/contacts"
            )
            query_method_not_allowed_response = client.delete(
                f"/api/staff/v1/employers/{employer_marker}/contacts/query"
            )
            detail_method_not_allowed_response = client.post(
                f"/api/staff/v1/employers/{employer_marker}/contacts/{contact_marker}"
            )
            unmatched_response = client.delete(
                f"/api/staff/v1/employers/{employer_marker}/contacts/{contact_marker}/{unmatched_marker}"
            )
    finally:
        event.remove(engine, "before_cursor_execute", record_sql)

    method_not_allowed_cases = [
        (create_method_not_allowed_response, "POST"),
        (query_method_not_allowed_response, "POST"),
        (detail_method_not_allowed_response, "GET"),
    ]
    for response, allow_header in method_not_allowed_cases:
        assert response.status_code == 405
        assert response.headers["Content-Type"] == "application/json"
        assert response.headers["Allow"] == allow_header
        assert response.headers["Cache-Control"] == "no-store"
        assert "Idempotency-Result-Version" not in response.headers
        assert "Idempotency-Replayed" not in response.headers
        assert response.json() == {"detail": "Method Not Allowed"}
        assert employer_marker not in response.text
        assert contact_marker not in response.text
        assert unmatched_marker not in response.text

    assert unmatched_response.status_code == 404
    assert unmatched_response.headers["Content-Type"] == "application/json"
    assert "Allow" not in unmatched_response.headers
    assert unmatched_response.headers["Cache-Control"] == "no-store"
    assert "Idempotency-Result-Version" not in unmatched_response.headers
    assert "Idempotency-Replayed" not in unmatched_response.headers
    assert unmatched_response.json() == {"detail": "Not Found"}
    assert employer_marker not in unmatched_response.text
    assert contact_marker not in unmatched_response.text
    assert unmatched_marker not in unmatched_response.text

    assert sql_statements == []
    assert {
        "employers": session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one(),
        "employer_contacts": session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one(),
        "command_receipts": session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one(),
        "audit_events": session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one(),
    } == baseline_counts


def test_staff_employer_contact_routes_do_not_log_contact_or_authority_markers(
    clean_tables,
    monkeypatch,
    session,
    caplog,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    caplog.set_level(logging.INFO)
    caplog.set_level(logging.INFO, logger="uvicorn")
    caplog.set_level(logging.INFO, logger="uvicorn.error")
    caplog.set_level(logging.INFO, logger="uvicorn.access")
    caplog.set_level(logging.INFO, logger="golden_rose")
    caplog.clear()

    employer_id = UUID("f3f3f3f3-3333-4333-8333-f3f3f3f3f3f3")
    create_employer_event_id = UUID("f4f4f4f4-4444-4444-8444-f4f4f4f4f4f4")
    employer_contact_id = UUID("f5f5f5f5-5555-4555-8555-f5f5f5f5f5f5")
    create_contact_event_id = UUID("f6f6f6f6-6666-4666-8666-f6f6f6f6f6f6")
    other_employer_id = UUID("f7f7f7f7-7777-4777-8777-f7f7f7f7f7f7")
    other_create_employer_event_id = UUID("f8f8f8f8-8888-4888-8888-f8f8f8f8f8f8")
    other_contact_id = UUID("f9f9f9f9-9999-4999-8999-f9f9f9f9f9f9")
    other_contact_event_id = UUID("fafafafa-aaaa-4aaa-8aaa-fafafafafafa")
    missing_contact_id = UUID("fbfbfbfb-bbbb-4bbb-8bbb-fbfbfbfbfbfb")
    body_marker = "contact-full-name-marker-rose"
    cursor_marker = "cursor-marker-rose"
    authority_marker = "authority-marker-rose"
    sql_marker = "sql-marker-rose"
    url_marker = "url-marker-rose"
    exception_marker = "exception-marker-rose"
    idempotency_key_marker = "fcfcfcfc-cccc-4ccc-8ccc-fcfcfcfcfcfc"

    app = create_app()
    with TestClient(app) as client:
        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            employer_id,
            create_employer_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 22, 10, 0, tzinfo=UTC)
        )
        create_employer_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "fdfdfdfd-dddd-4ddd-8ddd-fdfdfdfdfdfd"},
            json={
                "employer_type": "household",
                "display_name": "Contact Logging Parent",
            },
        )

        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            other_employer_id,
            other_create_employer_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 22, 11, 0, tzinfo=UTC)
        )
        other_employer_response = client.post(
            "/api/staff/v1/employers",
            headers={"Idempotency-Key": "abababab-1111-4111-8111-abababababab"},
            json={
                "employer_type": "business",
                "display_name": "Contact Logging Other Parent",
            },
        )

        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            employer_contact_id,
            create_contact_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 22, 12, 0, tzinfo=UTC)
        )
        create_contact_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts",
            headers={"Idempotency-Key": idempotency_key_marker},
            json={"full_name": body_marker},
        )

        app.dependency_overrides[get_identifier_factory] = lambda: FixedIdentifierFactory(
            other_contact_id,
            other_contact_event_id,
        )
        app.dependency_overrides[get_clock] = lambda: FixedClock(
            datetime(2026, 8, 12, 22, 13, 0, tzinfo=UTC)
        )
        other_contact_response = client.post(
            f"/api/staff/v1/employers/{other_employer_id}/contacts",
            headers={"Idempotency-Key": "cdcdcdcd-2222-4222-8222-cdcdcdcdcdcd"},
            json={"full_name": "other-contact-marker-rose"},
        )

        query_success_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts/query",
            json={"page_size": 1},
        )
        exact_success_response = client.get(
            f"/api/staff/v1/employers/{employer_id}/contacts/{employer_contact_id}"
        )
        validation_response = client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts/query",
            json={"page_size": 1, "cursor": cursor_marker},
        )
        missing_response = client.get(
            f"/api/staff/v1/employers/{employer_id}/contacts/{missing_contact_id}"
        )
        cross_parent_response = client.get(
            f"/api/staff/v1/employers/{employer_id}/contacts/{other_contact_id}"
        )

    changed_fields = session.execute(
        text("SELECT changed_fields FROM audit_events WHERE entity_id = :employer_contact_id"),
        {"employer_contact_id": employer_contact_id},
    ).scalar_one()

    denied_app = create_app()
    denied_app.dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
        actor_id=UUID("dededede-3333-4333-8333-dededededede"),
        role_name="synthetic_staff_without_contact_permissions",
        permissions=frozenset(),
    )
    with TestClient(denied_app, raise_server_exceptions=False) as denied_client:
        denied_response = denied_client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts?trace={url_marker}",
            headers={
                "Idempotency-Key": "efefefef-4444-4444-8444-efefefefefef",
                "X-Staff-Role": authority_marker,
                "X-Staff-Permissions": authority_marker,
                "X-Actor-Id": authority_marker,
            },
            json={"full_name": body_marker},
        )

    def raise_safe_persistence_error(**_: object):
        raise SafePersistenceError(f"{sql_marker} {url_marker} {exception_marker}")

    monkeypatch.setattr(
        employers_module,
        "create_employer_contact",
        raise_safe_persistence_error,
    )
    with TestClient(create_app(), raise_server_exceptions=False) as unavailable_client:
        unavailable_response = unavailable_client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts?trace={url_marker}",
            headers={"Idempotency-Key": "01010101-5555-4555-8555-010101010101"},
            json={"full_name": body_marker},
        )

    def raise_unexpected_error(**_: object):
        raise RuntimeError(f"{sql_marker} {url_marker} {authority_marker} {exception_marker}")

    monkeypatch.setattr(
        employers_module,
        "create_employer_contact",
        raise_unexpected_error,
    )
    with TestClient(create_app(), raise_server_exceptions=False) as error_client:
        unexpected_response = error_client.post(
            f"/api/staff/v1/employers/{employer_id}/contacts?trace={url_marker}",
            headers={"Idempotency-Key": "02020202-6666-4666-8666-020202020202"},
            json={"full_name": body_marker},
        )

    assert create_employer_response.status_code == 201
    assert other_employer_response.status_code == 201
    assert create_contact_response.status_code == 201
    assert other_contact_response.status_code == 201
    assert query_success_response.status_code == 200
    assert exact_success_response.status_code == 200
    assert validation_response.status_code == 422
    assert denied_response.status_code == 403
    assert missing_response.status_code == 404
    assert cross_parent_response.status_code == 404
    assert unavailable_response.status_code == 503
    assert unexpected_response.status_code == 500

    assert changed_fields == {
        "field_names": ["full_name"],
        "approved_values": {},
    }
    assert body_marker not in repr(changed_fields)

    relevant_log_text = "\n".join(
        record.getMessage()
        for record in caplog.records
        if record.name.startswith("golden_rose") or record.name.startswith("uvicorn")
    )

    assert body_marker not in relevant_log_text
    assert cursor_marker not in relevant_log_text
    assert str(employer_id) not in relevant_log_text
    assert str(employer_contact_id) not in relevant_log_text
    assert str(other_employer_id) not in relevant_log_text
    assert str(other_contact_id) not in relevant_log_text
    assert str(missing_contact_id) not in relevant_log_text
    assert idempotency_key_marker not in relevant_log_text
    assert authority_marker not in relevant_log_text
    assert sql_marker not in relevant_log_text
    assert url_marker not in relevant_log_text
    assert exception_marker not in relevant_log_text


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
