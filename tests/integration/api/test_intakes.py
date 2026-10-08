"""HTTP contract acceptance against disposable PostgreSQL, without browser claims."""

from dataclasses import replace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.exc import OperationalError

from golden_rose.api.dependencies import get_staff_principal
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.main import create_app

ROOT = "/api/staff/v1/intakes"
PERMISSIONS = frozenset(
    {"intake:read", "intake:draft:create", "intake:draft:revise"}
    | {
        f"{section}:{action}"
        for section in ("worker_residence", "party_address", "worksite_address")
        for action in ("read", "write")
    }
)
PRINCIPAL = StaffPrincipal(UUID("22222222-2222-4222-8222-222222222222"), "test", PERMISSIONS)


@pytest.fixture
def client(clean_tables):
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as instance:
        yield instance


def safe(response: Response, status: int) -> None:
    assert response.status_code == status, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "etag" not in response.headers and "last-modified" not in response.headers
    if status >= 400:
        assert response.headers["content-type"] == "application/problem+json"
        assert set(response.json()) == {"type", "title", "status", "detail", "code"}
        assert response.json()["status"] == status
        assert "idempotency-result-version" not in response.headers
        assert "idempotency-replayed" not in response.headers


def create(
    client: TestClient,
    *,
    key: UUID | str | None = None,
    content: dict[str, Any] | None = None,
    kind: str = "worker",
) -> Response:
    return cast(
        Response,
        client.post(
            ROOT,
            headers={"Idempotency-Key": str(key or uuid4())},
            json={"kind": kind, "content": content or {"phone": "+12025550123"}},
        ),
    )


def test_create_resume_retry_stale_and_address_minimization(client):
    key = uuid4()
    response = create(
        client,
        key=key,
        content={
            "full_name": "Fictional Worker",
            "phone": "+12025550123",
            "residential_address": {"line1": "23 Fictional Lane"},
        },
    )
    safe(response, 201)
    target = response.json()["current"]["summary"]["intake_id"]
    assert response.headers["location"] == f"{ROOT}/{target}"
    assert response.headers["idempotency-replayed"] == "false"
    assert response.headers["idempotency-result-version"] == "1"
    assert "23 Fictional Lane" not in response.text
    detail = client.get(f"{ROOT}/{target}")
    safe(detail, 200)
    assert detail.json()["candidate"]["full_name"] == "Fictional Worker"
    assert "23 Fictional Lane" not in detail.text
    summary = client.post(f"{ROOT}/query", json={"kind": "worker"})
    safe(summary, 200)
    assert summary.json()["items"][0]["intake_id"] == target
    assert "23 Fictional Lane" not in summary.text and "+12025550123" not in summary.text
    replay = create(
        client,
        key=key,
        content={
            "full_name": "Fictional Worker",
            "phone": "+12025550123",
            "residential_address": {"line1": "23 Fictional Lane"},
        },
    )
    safe(replay, 200)
    assert replay.headers["idempotency-replayed"] == "true"
    conflict = client.post(
        f"{ROOT}/{target}/revisions",
        headers={"Idempotency-Key": str(uuid4())},
        json={"expected_version": 2, "content": {"full_name": "Fictional Changed"}},
    )
    safe(conflict, 409)
    access = client.get(f"{ROOT}/{target}/addresses/worker_residence")
    safe(access, 200)
    assert access.json()["candidate"] == {"line1": "23 Fictional Lane"}


def test_worker_residential_address_revision_persists_for_fresh_read(client):
    created = create(client, content={"full_name": "Fictional Worker", "phone": "+12025550123"})
    safe(created, 201)
    target = created.json()["current"]["summary"]["intake_id"]
    response = client.post(
        f"{ROOT}/{target}/addresses/worker_residence/revisions",
        headers={"Idempotency-Key": str(uuid4())},
        json={
            "expected_version": 1,
            "address": {
                "line1": "2020 East Dr",
                "locality": "Brooklyn",
                "region": "New York",
                "postal_code": "11202",
                "country": "US",
            },
        },
    )
    safe(response, 200)
    assert "2020 East Dr" not in response.text
    first_read = client.get(f"{ROOT}/{target}/addresses/worker_residence")
    safe(first_read, 200)
    assert first_read.json()["candidate"] == {
        "line1": "2020 East Dr",
        "locality": "Brooklyn",
        "region": "NY",
        "postal_code": "11202",
        "country": "US",
    }
    second_read = client.get(f"{ROOT}/{target}/addresses/worker_residence")
    safe(second_read, 200)
    assert second_read.json() == first_read.json()


@pytest.mark.parametrize(
    "method,path,body,status",
    [
        ("get", "/not-a-uuid-sensitive", None, 422),
        ("get", "/00000000-0000-4000-8000-000000000000", None, 404),
        ("get", "/unknown/sensitive", None, 404),
        ("delete", "", None, 405),
        ("post", "/query", {"kind": "worker", "secret_marker": "sensitive-value"}, 422),
        ("post", "", {"kind": "worker", "content": {"full_name": 123}}, 422),
        ("post", "", {"kind": "worker", "content": {}}, 422),
    ],
)
def test_safe_validation_routing_errors(client, method, path, body, status):
    response = client.request(
        method, ROOT + path, json=body, headers={"Idempotency-Key": str(uuid4())}
    )
    safe(response, status)
    assert "sensitive" not in response.text
    assert "<html" not in response.text.lower()


def test_media_and_size_errors(client):
    response = client.post(
        ROOT, content='{"sensitive-value": true}', headers={"Content-Type": "text/plain"}
    )
    safe(response, 415)
    response = client.post(
        ROOT,
        content='{"sensitive-value":"' + "a" * 32768 + '"}',
        headers={"Content-Type": "application/json"},
    )
    safe(response, 413)
    response = client.post(
        ROOT, content='{"sensitive-value":', headers={"Content-Type": "application/json"}
    )
    safe(response, 422)
    assert "sensitive-value" not in response.text


def test_denied_and_unauthenticated_responses(client):
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        PRINCIPAL, permissions=frozenset()
    )
    safe(create(client), 403)

    def unauthenticated():
        raise HTTPException(401, "sensitive auth detail")

    client.app.dependency_overrides[get_staff_principal] = unauthenticated
    response = client.get(f"{ROOT}/{uuid4()}")
    safe(response, 401)
    assert "sensitive" not in response.text


def test_storage_failure_is_safe_retryable_503(client, monkeypatch):
    def unavailable(*args, **kwargs):
        raise OperationalError("sensitive SQL", {}, RuntimeError("sensitive database"))

    monkeypatch.setattr("golden_rose.api.staff.intakes.get_intake", unavailable)
    response = client.get(f"{ROOT}/{uuid4()}")
    safe(response, 503)
    assert response.headers["retry-after"] == "1"
    assert "sensitive" not in response.text


@pytest.mark.parametrize(
    "missing",
    ["intake:read", "worker_residence:read", "worker_residence:write", "intake:draft:revise"],
)
def test_address_requires_base_and_section_permissions(client, missing):
    created = create(client)
    safe(created, 201)
    target = created.json()["current"]["summary"]["intake_id"]
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        PRINCIPAL, permissions=PERMISSIONS - {missing}
    )
    response = client.post(
        f"{ROOT}/{target}/addresses/worker_residence/revisions",
        headers={"Idempotency-Key": str(uuid4())},
        json={"expected_version": 1, "address": {"line1": "23 Fictional Lane"}},
    )
    safe(response, 403)
    if missing in {"intake:read", "worker_residence:read"}:
        safe(client.get(f"{ROOT}/{target}/addresses/worker_residence"), 403)


def test_scope_is_404_for_detail_mutation_address_and_replay(client):
    created = create(client)
    safe(created, 201)
    target = created.json()["current"]["summary"]["intake_id"]
    key = uuid4()
    body = {"expected_version": 1, "address": {"line1": "Fictional Address"}}
    path = f"{ROOT}/{target}/addresses/worker_residence"
    safe(client.post(path + "/revisions", headers={"Idempotency-Key": str(key)}, json=body), 200)
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        PRINCIPAL, intake_scope=frozenset()
    )
    safe(client.get(f"{ROOT}/{target}"), 404)
    safe(client.get(path), 404)
    safe(client.post(path + "/revisions", headers={"Idempotency-Key": str(key)}, json=body), 404)
    safe(
        client.post(
            f"{ROOT}/{target}/revisions",
            headers={"Idempotency-Key": str(uuid4())},
            json={"expected_version": 2, "content": {"phone": "+12025550124"}},
        ),
        404,
    )


@pytest.mark.parametrize(
    "kind,section",
    [("worker", "party_address"), ("worker", "worksite_address"), ("employer", "worker_residence")],
)
def test_wrong_kind_section_is_422(client, kind, section):
    created = create(client, kind=kind)
    safe(created, 201)
    target = created.json()["current"]["summary"]["intake_id"]
    path = f"{ROOT}/{target}/addresses/{section}"
    safe(client.get(path), 422)
    safe(
        client.post(
            path + "/revisions",
            headers={"Idempotency-Key": str(uuid4())},
            json={"expected_version": 1, "address": {"line1": "Fictional"}},
        ),
        422,
    )


@pytest.mark.parametrize("later", ["finalize", "finalization"])
def test_future_workflow_routes_absent(client, later):
    response = client.post(f"{ROOT}/{uuid4()}/{later}", json={})
    safe(response, 404)


@pytest.mark.parametrize(
    "key",
    [
        "sensitive-invalid-key",
        "00000000-0000-0000-0000-000000000000",
        "22222222-2222-1222-8222-222222222222",
    ],
)
def test_invalid_idempotency_keys_are_value_safe(client, key):
    response = create(client, key=key)
    safe(response, 422)
    assert key not in response.text


def test_address_access_sink_receives_only_protected_metadata(client):
    created = create(
        client,
        content={
            "phone": "+12025550123",
            "residential_address": {"line1": "Fictional private access marker"},
        },
    )
    safe(created, 201)
    target = created.json()["current"]["summary"]["intake_id"]
    accesses = []
    client.app.state.intake_access_sink = lambda **fields: accesses.append(fields)
    safe(client.get(f"{ROOT}/{target}/addresses/worker_residence"), 200)
    assert accesses == [
        {"actor_id": PRINCIPAL.actor_id, "intake_id": UUID(target), "section": "worker_residence"}
    ]
    assert "Fictional private access marker" not in repr(accesses)
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        PRINCIPAL, permissions=frozenset({"intake:read"})
    )
    safe(client.get(f"{ROOT}/{target}/addresses/worker_residence"), 403)
    assert len(accesses) == 1


def test_complete_employer_summary_exposes_offer_without_private_terms(client):
    address = {
        "line1": "17 Fictional Road",
        "locality": "Fictional City",
        "country": "US",
        "region": "NY",
        "postal_code": "10001",
    }
    response = create(
        client,
        kind="employer",
        content={
            "employer_type": "business",
            "display_name": "Fictional Employer",
            "representative_name": "Fictional Representative",
            "phone": "+12025550123",
            "role_title": "Fictional Role",
            "duties_summary": "Fictional Duties",
            "worker_count": 2,
            "schedule": {"mode": "to_be_discussed"},
            "offer": {
                "minimum": "20.00",
                "currency": "USD",
                "basis": "hour",
                "per_worker": True,
                "terms": "Private fictional terms",
            },
            "party_address": address,
            "worksite_address": address,
        },
    )
    safe(response, 201)
    summary = response.json()["current"]["summary"]
    assert summary["complete"] and summary["missing_fields"] == []
    assert summary["offer"]["minimum"] == "20.00"
    assert "terms" not in summary["offer"]
    result = client.post(f"{ROOT}/query", json={"kind": "employer", "name_query": "Employer"})
    safe(result, 200)
    assert len(result.json()["items"]) == 1
    assert "Private fictional terms" not in result.text
    assert "17 Fictional Road" not in response.text and "17 Fictional Road" not in result.text


def test_complete_worker_and_cleared_address_updates_missing_section(client):
    response = create(
        client,
        content={
            "full_name": "Fictional Worker",
            "phone": "+12025550123",
            "interests": {"other_description": "Fictional interests"},
            "availability": {"mode": "flexible"},
            "residential_address": {
                "line1": "Fictional Road",
                "locality": "Fictional City",
                "country": "CA",
            },
        },
    )
    safe(response, 201)
    target = response.json()["current"]["summary"]["intake_id"]
    assert response.json()["current"]["summary"]["complete"]
    path = f"{ROOT}/{target}/addresses/worker_residence/revisions"
    response = client.post(
        path,
        headers={"Idempotency-Key": str(uuid4())},
        json={"expected_version": 1, "address": None},
    )
    safe(response, 200)
    assert response.json()["current"]["summary"]["missing_fields"] == ["worker_residence"]
    no_change = client.post(
        path,
        headers={"Idempotency-Key": str(uuid4())},
        json={"expected_version": 2, "address": None},
    )
    safe(no_change, 409)
    assert no_change.json()["code"] == "no_change"


def test_worker_revision_rejects_employer_content_and_unknown_address_section(client):
    response = create(client)
    safe(response, 201)
    target = response.json()["current"]["summary"]["intake_id"]
    safe(
        client.post(
            f"{ROOT}/{target}/revisions",
            headers={"Idempotency-Key": str(uuid4())},
            json={"expected_version": 1, "content": {"display_name": "Fictional"}},
        ),
        422,
    )
    safe(client.get(f"{ROOT}/{target}/addresses/unknown"), 422)
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        PRINCIPAL, intake_scope=frozenset()
    )
    safe(create(client), 403)


def test_address_read_storage_failure_is_safe(client, monkeypatch):
    response = create(client)
    safe(response, 201)
    target = response.json()["current"]["summary"]["intake_id"]

    def unavailable(*args, **kwargs):
        raise OperationalError("sensitive SQL", {}, RuntimeError("sensitive storage"))

    monkeypatch.setattr("golden_rose.api.staff.intakes.get_address", unavailable)
    response = client.get(f"{ROOT}/{target}/addresses/worker_residence")
    safe(response, 503)
    assert "sensitive" not in response.text
