from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from golden_rose.api.dependencies import get_db_session, get_settings
from golden_rose.api.staff import employer_outputs
from golden_rose.application.shift_needs import ShiftNeedResult, StaffingRequestResult
from golden_rose.main import create_app
from tests.unit.test_employer_finalization_outputs import PARTY, content

PATHS = ["addresses", "worksites", "worksites/address", "requests"]


def path(section) -> Any:
    family, _, suffix = section.partition("/")
    return f"/api/staff/v1/employers/{uuid4()}/{family}/{uuid4()}" + (
        f"/{suffix}" if suffix else ""
    )


def projection(section) -> dict[str, Any]:
    base = {"employer_id": uuid4(), "version": 1}
    if section == "addresses":
        return {**base, "employer_address_id": uuid4(), "purpose": "business", "address": PARTY}
    if section.startswith("worksites"):
        return {
            **base,
            "worksite_id": uuid4(),
            **(
                {"address": PARTY}
                if section.endswith("address")
                else {
                    "location_verification_status": "supplied",
                    "service_area_status": "unassigned",
                    "map_area_status": "pending",
                }
            ),
        }
    facts = content()
    return {
        **base,
        "staffing_request_id": uuid4(),
        "employer_contact_id": uuid4(),
        "worksite_id": uuid4(),
        "employer_address_id": None,
        "request_type": "household",
        "request_status": "draft",
        "source_channel": "staff_entry",
        **{
            name: facts[name]
            for name in ("role_title", "duties_summary", "worker_count", "schedule", "offer")
        },
        **{name: datetime.now(UTC) for name in ("created_at", "received_at", "updated_at")},
    }


def shift_projection(**changes: Any) -> dict[str, Any]:
    values = {
        "shift_need_id": uuid4(),
        "employer_id": uuid4(),
        "staffing_request_id": uuid4(),
        "request_version_at_creation": 2,
        "shift_status": "pending_review",
        "role_title": "Home aide",
        "worker_count": 1,
        "starts_at": datetime(2026, 10, 1, 13, 0, tzinfo=UTC),
        "ends_at": datetime(2026, 10, 1, 17, 0, tzinfo=UTC),
        "time_zone": "America/New_York",
        "notes": None,
        "version": 2,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    values.update(changes)
    return values


@pytest.fixture
def http(monkeypatch) -> Iterator[Any]:
    app = create_app(engine_factory=lambda: Mock())
    app.dependency_overrides[get_db_session] = lambda: object()
    reader, sink = Mock(), Mock()
    monkeypatch.setattr(employer_outputs, "read_employer_output", reader)
    app.state.employer_output_access_sink = sink
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, reader, sink


@pytest.mark.parametrize("section", PATHS)
def test_safe_exact_projections(http, section):
    client, reader, sink = http
    reader.return_value = projection(section)
    response = client.get(path(section))
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "etag" not in response.headers
    if section in {"addresses", "worksites/address"}:
        assert set(sink.call_args.kwargs) == {"actor_id", "employer_id", "output_id", "section"}
    else:
        assert PARTY["line1"] not in response.text
        sink.assert_not_called()
    if section == "requests":
        assert response.json()["offer"]["terms"] == content()["offer"]["terms"]
        assert response.json()["employer_address_id"] is None


@pytest.mark.parametrize("section", PATHS)
def test_develop_blocked(http, section):
    client, reader, sink = http
    settings = get_settings().model_copy(update={"environment": "develop"})
    client.app.dependency_overrides[get_settings] = lambda: settings
    assert client.get(path(section)).status_code == 403
    reader.assert_not_called()
    sink.assert_not_called()


@pytest.mark.parametrize("section", ["addresses", "worksites/address"])
@pytest.mark.parametrize("failure", ["sink", "projection"])
def test_failed_reveal_is_value_safe(http, section, failure):
    client, reader, sink = http
    reader.return_value = projection(section)
    if failure == "sink":
        sink.side_effect = OSError("private")
    else:
        reader.return_value["private"] = "private"
    response = client.get(path(section))
    assert response.status_code == 503
    assert "private" not in response.text and PARTY["line1"] not in response.text
    if failure == "projection":
        sink.assert_not_called()


@pytest.mark.parametrize("family", ["addresses", "worksites", "requests"])
def test_routing_errors_do_not_reflect_input(http, family):
    client, reader, _ = http
    response = client.get(f"/api/staff/v1/employers/private/{family}/private")
    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert "private" not in response.text
    reader.assert_not_called()


def test_unexpected_failure_is_safe(http):
    client, reader, _ = http
    reader.side_effect = RuntimeError("private driver")
    response = client.get(path("requests"))
    assert response.status_code == 503
    assert "private" not in response.text


@pytest.mark.parametrize("kind", ["addresses", "worksites", "requests"])
def test_query_route_preserves_empty_cursor(http, monkeypatch, kind):
    client, reader, sink = http
    query = Mock(return_value={"items": [], "next_cursor": None})
    monkeypatch.setattr(employer_outputs, "query_employer_outputs", query)
    response = client.post(f"/api/staff/v1/employers/{uuid4()}/{kind}/query", json={})
    assert response.status_code == 200, response.text
    assert response.json() == {"items": [], "next_cursor": None}
    assert response.headers["cache-control"] == "no-store"
    assert query.call_args.kwargs["kind"] == kind
    reader.assert_not_called()
    sink.assert_not_called()


@pytest.mark.parametrize("kind", ["addresses", "worksites", "requests"])
def test_query_develop_blocked(http, monkeypatch, kind):
    client, _, _ = http
    query = Mock()
    monkeypatch.setattr(employer_outputs, "query_employer_outputs", query)
    settings = get_settings().model_copy(update={"environment": "develop"})
    client.app.dependency_overrides[get_settings] = lambda: settings
    assert (
        client.post(f"/api/staff/v1/employers/{uuid4()}/{kind}/query", json={}).status_code == 403
    )
    query.assert_not_called()


@pytest.mark.parametrize("body", [{"page_size": 51}, {"phone": "private"}, {"cursor": "x" * 1025}])
def test_query_validation_is_safe(http, monkeypatch, body):
    client, _, _ = http
    query = Mock()
    monkeypatch.setattr(employer_outputs, "query_employer_outputs", query)
    response = client.post(f"/api/staff/v1/employers/{uuid4()}/requests/query", json=body)
    assert response.status_code == 422
    assert "private" not in response.text
    query.assert_not_called()


def test_request_list_rejects_terms(http, monkeypatch):
    client, _, _ = http
    detail = projection("requests")
    item = {
        k: detail[k]
        for k in (
            "staffing_request_id",
            "employer_id",
            "version",
            "request_status",
            "role_title",
            "worker_count",
            "offer",
        )
    }
    query = Mock(return_value={"items": [item], "next_cursor": None})
    monkeypatch.setattr(employer_outputs, "query_employer_outputs", query)
    response = client.post(f"/api/staff/v1/employers/{uuid4()}/requests/query", json={})
    assert response.status_code == 503
    assert "Fictional offer terms" not in response.text


def test_submit_request_for_review_route_sets_idempotency_headers(http, monkeypatch):
    client, reader, sink = http
    request_id = uuid4()
    detail = projection("requests")
    detail["staffing_request_id"] = request_id
    detail["request_status"] = "pending_review"
    submit = Mock(
        return_value=StaffingRequestResult(
            {
                "command_id": uuid4(),
                "result_record_version": 3,
                "event_type": "staffing_request.submitted_for_review",
                "current": detail,
            },
            True,
        )
    )
    monkeypatch.setattr(employer_outputs, "submit_staffing_request_for_review", submit)

    response = client.post(
        f"/api/staff/v1/employers/{detail['employer_id']}/requests/{request_id}/submit-review",
        json={"expected_version": 2, "reason_text": "Ready for supervisor review"},
        headers={"Idempotency-Key": str(uuid4())},
    )

    assert response.status_code == 200, response.text
    assert response.headers["idempotency-replayed"] == "true"
    assert response.headers["idempotency-result-version"] == "3"
    assert response.json()["event_type"] == "staffing_request.submitted_for_review"
    assert submit.call_args.kwargs["body"].expected_version == 2
    reader.assert_not_called()
    sink.assert_not_called()


def test_submit_shift_need_for_review_route_sets_idempotency_headers(http, monkeypatch):
    client, reader, sink = http
    employer_id = uuid4()
    request_id = uuid4()
    shift_need_id = uuid4()
    detail = shift_projection(
        employer_id=employer_id,
        staffing_request_id=request_id,
        shift_need_id=shift_need_id,
    )
    submit = Mock(
        return_value=ShiftNeedResult(
            {
                "command_id": uuid4(),
                "result_record_version": 2,
                "event_type": "shift_need.submitted_for_review",
                "current": detail,
            },
            False,
        )
    )
    monkeypatch.setattr(employer_outputs, "submit_shift_need_for_review", submit)

    response = client.post(
        f"/api/staff/v1/employers/{employer_id}/requests/{request_id}"
        f"/shift-needs/{shift_need_id}/submit-review",
        json={"expected_version": 1, "reason_text": "Ready for supervisor review"},
        headers={"Idempotency-Key": str(uuid4())},
    )

    assert response.status_code == 200, response.text
    assert response.headers["idempotency-replayed"] == "false"
    assert response.headers["idempotency-result-version"] == "2"
    assert response.json()["event_type"] == "shift_need.submitted_for_review"
    assert submit.call_args.kwargs["body"].reason_text == "Ready for supervisor review"
    reader.assert_not_called()
    sink.assert_not_called()
