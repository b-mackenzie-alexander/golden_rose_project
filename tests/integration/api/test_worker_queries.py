"""Worker discovery against canonical records with tied creation timestamps."""

from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from golden_rose.api.dependencies import get_clock, get_staff_principal
from golden_rose.api.staff.intake_schemas import CreateIntakeRequest
from golden_rose.persistence.models import audit_events, command_receipts
from tests.integration.api.test_intake_finalizations import client as client
from tests.integration.api.test_intake_review_workflows import ROOT, command

QUERY = "/api/staff/v1/workers/query"


@pytest.fixture
def reader(client):
    principal = client.app.dependency_overrides[get_staff_principal]()
    principal = replace(principal, permissions=principal.permissions | {"worker:read"})
    client.app.dependency_overrides[get_staff_principal] = lambda: principal
    client.app.dependency_overrides[get_clock] = lambda: SimpleNamespace(
        now=lambda: datetime(2026, 9, 14, 12, tzinfo=UTC)
    )
    return client, principal


def create_worker(client: TestClient, name: str) -> str:
    body = {
        "kind": "worker",
        "content": {
            "full_name": name,
            "phone": "202-555-0151",
            "interests": {"other_description": "Fictional gardening"},
            "availability": {"mode": "flexible"},
            "residential_address": {
                "line1": "10 Fictional Road",
                "locality": "Fictional City",
                "country": "US",
                "region": "NY",
                "postal_code": "10001",
            },
        },
    }
    CreateIntakeRequest.model_validate(body)
    target = command(client, ROOT, body, 201).json()["current"]["summary"]["intake_id"]
    reviewed = command(
        client,
        f"{ROOT}/{target}/reviews",
        {
            "expected_version": 1,
            "outcome": "intake_reviewed",
        },
    ).json()["current"]
    finalized = command(
        client,
        f"{ROOT}/{target}/finalizations",
        {
            "expected_version": 2,
            "review_id": reviewed["latest_review"]["review_id"],
        },
        201,
    ).json()
    return str(finalized["finalization"]["worker"]["id"])


def test_worker_query_stable_keyset_and_minimal_results(reader, session):
    client, _ = reader
    identities = [create_worker(client, f"Fictional Search {index}") for index in range(3)]
    before = [
        session.scalar(select(func.count()).select_from(table))
        for table in (audit_events, command_receipts)
    ]
    body = {"name_query": "fictional search", "page_size": 1}
    found = []
    for _ in range(3):
        response = client.post(QUERY, json=body)
        assert response.status_code == 200, response.text
        assert response.headers["cache-control"] == "no-store"
        page = response.json()
        assert len(page["items"]) == 1
        item = page["items"][0]
        assert set(item) == {"worker_id", "full_name", "version"}
        found.append(item["worker_id"])
        body["cursor"] = page["next_cursor"]
    assert body["cursor"] is None
    assert found == sorted(identities, key=UUID, reverse=True)
    assert before == [
        session.scalar(select(func.count()).select_from(table))
        for table in (audit_events, command_receipts)
    ]


@pytest.mark.parametrize("fragment", ["%_", "A_B", "A\\B"])
def test_worker_query_escapes_literal_wildcards(reader, fragment):
    client, _ = reader
    target = create_worker(client, f"Fictional {fragment} Worker")
    create_worker(client, "Fictional AXB Worker")
    response = client.post(QUERY, json={"name_query": fragment})
    assert response.status_code == 200, response.text
    assert [row["worker_id"] for row in response.json()["items"]] == [target]


def test_worker_reference_queries_respect_scope_and_missing(reader):
    client, principal = reader
    target = create_worker(client, "Fictional Reference Worker")
    response = client.post(QUERY, json={"reference": target})
    assert response.status_code == 200, response.text
    assert [row["worker_id"] for row in response.json()["items"]] == [target]
    missing = client.post(QUERY, json={"reference": str(uuid4())})
    assert missing.json() == {"items": [], "next_cursor": None}
    scoped = replace(principal, worker_scope=frozenset())
    client.app.dependency_overrides[get_staff_principal] = lambda: scoped
    denied = client.post(QUERY, json={"reference": target})
    assert denied.status_code == 200
    assert denied.json() == missing.json()


def test_worker_query_cursor_rejects_scope_change_and_revoked_permission(reader):
    client, principal = reader
    first = create_worker(client, "Fictional Cursor Worker A")
    create_worker(client, "Fictional Cursor Worker B")
    body = {"name_query": "Fictional Cursor", "page_size": 1}
    response = client.post(QUERY, json=body)
    assert response.status_code == 200, response.text
    body["cursor"] = response.json()["next_cursor"]
    assert body["cursor"]
    scoped = replace(principal, worker_scope=frozenset({UUID(first)}))
    client.app.dependency_overrides[get_staff_principal] = lambda: scoped
    changed = client.post(QUERY, json=body)
    assert changed.status_code == 422
    assert changed.json()["code"] == "invalid_cursor"
    revoked = replace(principal, permissions=principal.permissions - {"worker:read"})
    client.app.dependency_overrides[get_staff_principal] = lambda: revoked
    assert client.post(QUERY, json=body).status_code == 403
