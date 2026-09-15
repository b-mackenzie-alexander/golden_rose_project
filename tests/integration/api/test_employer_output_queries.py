"""Parent query acceptance without bypassing canonical creation authority."""

from dataclasses import replace
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from golden_rose.api.dependencies import get_staff_principal
from golden_rose.application.intake_cursors import binding, encode_cursor
from golden_rose.persistence.models import audit_events, command_receipts, worksites
from tests.integration.api.test_contact_details import canonical
from tests.integration.api.test_intake_finalizations import client as client
from tests.unit.test_employer_finalization_outputs import PARTY, WORKSITE


@pytest.fixture
def output(client) -> tuple[Any, ...]:
    _, refs, principal = canonical(client, "business")
    reader = replace(
        principal, permissions=principal.permissions | {"worksite:read", "staffing_request:read"}
    )
    client.app.dependency_overrides[get_staff_principal] = lambda: reader
    return refs, reader


def url(refs, kind) -> str:
    return f"/api/staff/v1/employers/{refs['employer']['id']}/{kind}/query"


@pytest.mark.parametrize(
    "kind,key,id_name,fields",
    [
        (
            "addresses",
            "business_address",
            "employer_address_id",
            {"employer_address_id", "employer_id", "version", "purpose"},
        ),
        ("worksites", "worksite", "worksite_id", {"worksite_id", "employer_id", "version"}),
        (
            "requests",
            "request",
            "staffing_request_id",
            {
                "staffing_request_id",
                "employer_id",
                "version",
                "request_status",
                "role_title",
                "worker_count",
                "offer",
            },
        ),
    ],
)
def test_query_minimized_parent_results_without_writes(
    client, session, output, kind, key, id_name, fields
):
    refs, _ = output
    canonical(client, "business")
    before = [
        session.scalar(select(func.count()).select_from(t))
        for t in (audit_events, command_receipts)
    ]
    response = client.post(url(refs, kind), json={"page_size": 1})
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    assert "idempotency-replayed" not in response.headers
    page = response.json()
    assert page["next_cursor"] is None
    assert len(page["items"]) == 1
    item = page["items"][0]
    assert set(item) == fields
    assert item[id_name] == refs[key]["id"]
    assert PARTY["line1"] not in response.text and WORKSITE["line1"] not in response.text
    if kind == "requests":
        assert set(item["offer"]) == {
            "minimum",
            "maximum",
            "currency",
            "basis",
            "per_worker",
            "negotiable",
        }
    assert before == [
        session.scalar(select(func.count()).select_from(t))
        for t in (audit_events, command_receipts)
    ]


@pytest.mark.parametrize(
    "kind,permission",
    [
        ("addresses", "party_address:read"),
        ("worksites", "worksite:read"),
        ("requests", "staffing_request:read"),
        ("addresses", "employer:read"),
        ("worksites", "employer:read"),
        ("requests", "employer:read"),
    ],
)
def test_query_permissions_precede_invalid_cursor(client, output, kind, permission):
    refs, reader = output
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        reader, permissions=reader.permissions - {permission}
    )
    assert client.post(url(refs, kind), json={"cursor": "invalid"}).status_code == 403


@pytest.mark.parametrize("kind", ["addresses", "worksites", "requests"])
def test_missing_parent_is_404(client, output, kind):
    refs, _ = output
    response = client.post(url(refs, kind).replace(refs["employer"]["id"], str(uuid4())), json={})
    assert response.status_code == 404


def test_household_has_empty_business_addresses(client):
    _, refs, _ = canonical(client)
    response = client.post(url(refs, "addresses"), json={})
    assert response.status_code == 200, response.text
    assert response.json() == {"items": [], "next_cursor": None}


@pytest.mark.parametrize(
    "position,expected", [("same", 0), ("later", 1), ("higher_id", 1), ("lower_id", 0)]
)
def test_postgres_cursor_boundaries(client, session, output, position, expected):
    refs, reader = output
    target = UUID(refs["worksite"]["id"])
    instant = session.scalar(
        select(worksites.c.created_at).where(worksites.c.worksite_id == target)
    )
    identity = target
    if position == "later":
        instant += timedelta(seconds=1)
    elif position == "higher_id":
        identity = UUID(int=target.int + 1)
    elif position == "lower_id":
        identity = UUID(int=target.int - 1)
    # Multiple children require linking. Signed boundaries exercise real SQL
    # keysets without disabling the current creation guards.
    bound = binding(
        reader,
        {
            "kind": "canonical_employer_worksites",
            "parent": refs["employer"]["id"],
            "order": "created_at_desc_id_desc",
            "scope": "shared_synthetic_employers",
            "query": {"page_size": 1},
        },
    )
    cursor = encode_cursor(bound, {"at": instant.isoformat(), "id": str(identity)})
    response = client.post(url(refs, "worksites"), json={"page_size": 1, "cursor": cursor})
    assert response.status_code == 200, response.text
    assert len(response.json()["items"]) == expected
    assert response.json()["next_cursor"] is None
    assert (
        client.post(url(refs, "addresses"), json={"page_size": 1, "cursor": cursor}).status_code
        == 422
    )
