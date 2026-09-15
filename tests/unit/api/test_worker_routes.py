from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from golden_rose.api.dependencies import get_db_session, get_settings
from golden_rose.api.staff import workers
from golden_rose.main import create_app


@pytest.fixture
def http(monkeypatch):
    engine: Any = Mock()
    app = create_app(engine_factory=lambda: engine)
    app.dependency_overrides[get_db_session] = lambda: object()
    reader = Mock()
    sink = Mock()
    app.state.worker_access_sink = sink
    monkeypatch.setattr(workers, "read_worker", reader)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, reader, sink


def projection(section: str, worker_id: UUID) -> dict[str, Any]:
    base: dict[str, Any] = {"worker_id": worker_id, "version": 1}
    if section == "":
        return {
            **base,
            "full_name": "Fictional Worker",
            "contact_id": uuid4(),
            "residence_id": uuid4(),
            "preferences_id": uuid4(),
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
    if section == "/contact":
        return {**base, "worker_contact_id": uuid4(), "phone": "+12025550123"}
    if section == "/residence":
        return {
            **base,
            "worker_residence_id": uuid4(),
            "address": {
                "line1": "10 Fictional Road",
                "locality": "Fictional City",
                "country": "US",
            },
        }
    return {
        **base,
        "worker_preferences_id": uuid4(),
        "self_reported": True,
        "interests": {"other_description": "Fictional gardening"},
        "availability": {"mode": "flexible"},
    }


@pytest.mark.parametrize("section", ["", "/contact", "/residence", "/preferences"])
def test_worker_routes_project_only_canonical_section_with_safe_headers(http, section):
    client, reader, sink = http
    target = uuid4()
    reader.return_value = projection(section, target)
    response = client.get(f"/api/staff/v1/workers/{target}{section}")
    assert response.status_code == 200, response.text
    assert response.json()["worker_id"] == str(target)
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "etag" not in response.headers
    assert "last-modified" not in response.headers
    assert reader.call_args.kwargs["section"] == (section.lstrip("/") or "identity")
    assert reader.call_args.kwargs["worker_id"] == target
    if section == "/residence":
        assert sink.call_args.kwargs["worker_id"] == target
        assert set(sink.call_args.kwargs) == {"worker_id", "actor_id"}
    else:
        sink.assert_not_called()
        assert "10 Fictional Road" not in response.text


@pytest.mark.parametrize("section", ["", "/contact", "/residence", "/preferences"])
def test_worker_routes_block_develop_before_service(http, section):
    client, reader, sink = http
    settings = get_settings().model_copy(update={"environment": "develop"})
    client.app.dependency_overrides[get_settings] = lambda: settings
    response = client.get(f"/api/staff/v1/workers/{uuid4()}{section}")
    assert response.status_code == 403
    reader.assert_not_called()
    sink.assert_not_called()


@pytest.mark.parametrize("path,status", [("private-invalid", 422), ("unknown/path", 404)])
def test_worker_routing_errors_are_value_safe(http, path, status):
    client, reader, _ = http
    response = client.get(f"/api/staff/v1/workers/{path}")
    assert response.status_code == status
    assert response.headers["content-type"] == "application/problem+json"
    assert response.headers["cache-control"] == "no-store"
    assert "private-invalid" not in response.text
    reader.assert_not_called()


def test_worker_read_unexpected_failure_is_safe(http):
    client, reader, sink = http
    reader.side_effect = RuntimeError("private driver credentials")
    response = client.get(f"/api/staff/v1/workers/{uuid4()}/residence")
    assert response.status_code == 503
    assert "private" not in response.text
    assert response.headers["retry-after"] == "1"
    sink.assert_not_called()


def test_worker_residence_sink_failure_prevents_disclosure(http):
    client, reader, sink = http
    target = uuid4()
    reader.return_value = projection("/residence", target)
    sink.side_effect = OSError("private logging failure")
    response = client.get(f"/api/staff/v1/workers/{target}/residence")
    assert response.status_code == 503
    assert "10 Fictional Road" not in response.text


def test_worker_invalid_projection_is_not_disclosed(http):
    client, reader, sink = http
    target = uuid4()
    reader.return_value = {**projection("", target), "address": "private-value"}
    response = client.get(f"/api/staff/v1/workers/{target}")
    assert response.status_code == 503
    assert "private-value" not in response.text
    sink.assert_not_called()


def test_worker_query_route_is_not_captured_by_uuid_route(http, monkeypatch):
    client, reader, sink = http
    query = Mock(return_value={"items": [], "next_cursor": None})
    monkeypatch.setattr(workers, "query_workers", query)
    response = client.post("/api/staff/v1/workers/query", json={"name_query": " Fictional "})
    assert response.status_code == 200, response.text
    assert response.json() == {"items": [], "next_cursor": None}
    assert query.call_args.kwargs["request"].name_query == "Fictional"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    assert "idempotency-replayed" not in response.headers
    reader.assert_not_called()
    sink.assert_not_called()


@pytest.mark.parametrize(
    "body", [{}, {"name_query": "x"}, {"name_query": "Fictional", "phone": "private-value"}]
)
def test_worker_query_invalid_body_is_safe(http, monkeypatch, body):
    client, _, _ = http
    query = Mock()
    monkeypatch.setattr(workers, "query_workers", query)
    response = client.post("/api/staff/v1/workers/query", json=body)
    assert response.status_code == 422
    assert "private-value" not in response.text
    query.assert_not_called()


def test_worker_query_develop_is_blocked(http, monkeypatch):
    client, _, _ = http
    query = Mock()
    monkeypatch.setattr(workers, "query_workers", query)
    settings = get_settings().model_copy(update={"environment": "develop"})
    client.app.dependency_overrides[get_settings] = lambda: settings
    response = client.post("/api/staff/v1/workers/query", json={"name_query": "Fictional"})
    assert response.status_code == 403
    query.assert_not_called()
