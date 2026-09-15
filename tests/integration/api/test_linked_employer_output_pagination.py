"""Real returned-cursor traversal over finalized children of a reused employer."""

from dataclasses import replace
from datetime import timedelta
from types import SimpleNamespace
from typing import Any

import pytest

from golden_rose.api.dependencies import SystemClock, get_clock, get_staff_principal
from tests.integration.api.test_intake_review_workflows import ROOT, command
from tests.integration.test_intake_link_authority import (
    AUTHORITY_TABLES,
    EMPLOYER_TABLES,
    LINKER,
    canonical,
    draft_employer,
    link,
    reference,
    review,
    rows,
)
from tests.integration.test_intake_link_authority import client as client
from tests.integration.test_intake_link_authority import migration_database as migration_database
from tests.unit.test_employer_finalization_outputs import PARTY, WORKSITE

COLLECTIONS = {
    "addresses": ("employer_addresses", "business_address", "employer_address_id"),
    "worksites": ("worksites", "worksite", "worksite_id"),
    "requests": ("staffing_requests", "request", "staffing_request_id"),
}
PERMISSIONS = {
    "addresses": "party_address:read",
    "worksites": "worksite:read",
    "requests": "staffing_request:read",
}
READ_TABLES = (
    *AUTHORITY_TABLES,
    *EMPLOYER_TABLES,
    "entity_authorities",
    "intakes",
    "intake_addresses",
    "intake_links",
    "intake_reviews",
    "intake_review_payloads",
    "intake_history_payloads",
    "intake_finalizations",
)


def snapshot(database) -> dict[str, Any]:
    return {table: rows(database, table) for table in READ_TABLES}


def url(parent, kind) -> str:
    return f"/api/staff/v1/employers/{parent}/{kind}/query"


def set_reader(client, principal) -> None:
    client.app.dependency_overrides[get_staff_principal] = lambda: principal


@pytest.fixture
def linked_outputs(client, migration_database) -> tuple[Any, ...]:
    first = canonical(client, "business")
    outputs = [first]
    # Use the supported clock dependency, not updates to immutable canonical rows.
    instant = SystemClock().now() + timedelta(minutes=1)
    fixed_clock = SimpleNamespace(now=lambda: instant)
    for index in range(3):
        target = draft_employer(client, "business")
        link(migration_database, target, 1, reference(first["employer"]))
        body = review(client, target, 2)
        client.app.dependency_overrides[get_clock] = lambda: fixed_clock
        try:
            result = command(client, f"{ROOT}/{target}/finalizations", body, 201).json()[
                "finalization"
            ]
        finally:
            client.app.dependency_overrides.pop(get_clock)
        assert reference(result["employer"]) == reference(first["employer"])
        assert result["employer"]["disposition"] == "reused"
        for _, key, _ in COLLECTIONS.values():
            assert result[key]["disposition"] == "created"
        outputs.append(result)
        if index == 0:
            # Include unrelated children to exercise parent filtering during traversal.
            other = canonical(client, "business")
    reader = replace(LINKER, permissions=LINKER.permissions | set(PERMISSIONS.values()))
    set_reader(client, reader)
    return outputs, other, reader


def assert_minimized(response, kind, parent) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    assert "idempotency-replayed" not in response.headers
    assert PARTY["line1"] not in response.text
    assert WORKSITE["line1"] not in response.text
    page = response.json()
    assert set(page) == {"items", "next_cursor"}
    fields = {COLLECTIONS[kind][2], "employer_id", "version"}
    if kind == "addresses":
        fields |= {"purpose"}
    elif kind == "requests":
        fields |= {"request_status", "role_title", "worker_count", "offer"}
    for item in page["items"]:
        assert set(item) == fields
        assert item["employer_id"] == parent
        if kind == "requests":
            assert set(item["offer"]) == {
                "minimum",
                "maximum",
                "currency",
                "basis",
                "per_worker",
                "negotiable",
            }
    return dict(page)


@pytest.mark.parametrize("page_size", [1, 2])
def test_returned_cursors_traverse_exact_same_parent_outputs(
    client, migration_database, linked_outputs, page_size
):
    outputs, other, _ = linked_outputs
    parent = outputs[0]["employer"]["id"]
    before = snapshot(migration_database)
    for kind, (table, key, id_name) in COLLECTIONS.items():
        current = [row for row in before[table] if str(row["employer_id"]) == parent]
        times = [row["created_at"] for row in current]
        assert times.count(max(times)) == 3
        expected = [
            str(row[id_name])
            for row in sorted(
                current, key=lambda row: (row["created_at"], row[id_name]), reverse=True
            )
        ]
        assert len(expected) == len(outputs) == 4
        assert set(expected) == {output[key]["id"] for output in outputs}
        cursor = None
        seen, cursors = [], set()
        for offset in range(0, len(expected), page_size):
            query = {"page_size": page_size}
            if cursor is not None:
                query["cursor"] = cursor
            page = assert_minimized(client.post(url(parent, kind), json=query), kind, parent)
            identities = [item[id_name] for item in page["items"]]
            assert identities == expected[offset : offset + page_size]
            assert other[key]["id"] not in identities
            seen.extend(identities)
            cursor = page["next_cursor"]
            if offset + page_size < len(expected):
                assert isinstance(cursor, str) and cursor
                assert cursor not in cursors
                cursors.add(cursor)
            else:
                assert cursor is None
        assert seen == expected
        assert len(seen) == len(set(seen))
    assert snapshot(migration_database) == before


@pytest.mark.parametrize("kind", COLLECTIONS)
def test_returned_cursor_binding_and_permission_revocation(
    client, migration_database, linked_outputs, kind
):
    outputs, other, reader = linked_outputs
    parent = outputs[0]["employer"]["id"]
    before = snapshot(migration_database)
    page = assert_minimized(client.post(url(parent, kind), json={"page_size": 1}), kind, parent)
    cursor = page["next_cursor"]
    assert isinstance(cursor, str) and cursor
    query = {"page_size": 1, "cursor": cursor}
    other_kind = next(candidate for candidate in COLLECTIONS if candidate != kind)
    for endpoint, body in (
        (url(other["employer"]["id"], kind), query),
        (url(parent, other_kind), query),
        (url(parent, kind), {**query, "page_size": 2}),
    ):
        response = client.post(endpoint, json=body)
        assert response.status_code == 422, response.text
        assert response.json()["code"] == "invalid_cursor"
    for permission in (PERMISSIONS[kind], "employer:read"):
        revoked = replace(reader, permissions=reader.permissions - {permission})
        set_reader(client, revoked)
        response = client.post(url(parent, kind), json=query)
        assert response.status_code == 403, response.text
        assert response.json()["code"] == "forbidden"
    set_reader(client, reader)
    resumed = assert_minimized(client.post(url(parent, kind), json=query), kind, parent)
    id_name = COLLECTIONS[kind][2]
    assert len(resumed["items"]) == 1
    assert resumed["items"][0][id_name] != page["items"][0][id_name]
    assert snapshot(migration_database) == before
