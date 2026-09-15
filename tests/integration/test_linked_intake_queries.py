"""Recovery lists use authorized effective facts before bounded pagination."""

from dataclasses import replace
from uuid import UUID

import pytest

from golden_rose.api.dependencies import get_staff_principal
from tests.integration.api.test_intake_review_workflows import ROOT, command
from tests.integration.test_intake_link_authority import (
    LINKER,
    canonical,
    draft_employer,
    link,
    reference,
    review,
)
from tests.integration.test_intake_link_authority import client as client
from tests.integration.test_intake_migrations import migration_database as migration_database


def test_linked_worker_list_search_pagination_and_finalized_completeness(
    client, migration_database
):
    refs = canonical(client)
    targets = []
    for _ in range(2):
        target = command(
            client, ROOT, {"kind": "worker", "content": {"phone": "202-555-0199"}}, 201
        ).json()["current"]["summary"]["intake_id"]
        link(migration_database, target, 1, reference(refs["worker"]))
        targets.append(target)
    detail = client.get(f"{ROOT}/{targets[0]}").json()
    name = detail["summary"]["display_name"]
    query = {"kind": "worker", "name_query": name, "page_size": 1}
    first = client.post(f"{ROOT}/query", json=query).json()
    assert len(first["items"]) == 1 and first["next_cursor"]
    second = client.post(f"{ROOT}/query", json={**query, "cursor": first["next_cursor"]}).json()
    assert {row["intake_id"] for row in first["items"] + second["items"]} == set(targets)
    assert all(
        row["complete"] and row["missing_fields"] == [] and row["display_name"] == name
        for row in first["items"] + second["items"]
    )
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        LINKER, worker_scope=frozenset({UUID(refs["worker"]["id"])})
    )
    changed = client.post(f"{ROOT}/query", json={**query, "cursor": first["next_cursor"]})
    assert changed.status_code == 422 and changed.json()["code"] == "invalid_cursor"
    client.app.dependency_overrides[get_staff_principal] = lambda: LINKER
    body = review(client, targets[0], 2)
    command(client, f"{ROOT}/{targets[0]}/finalizations", body, 201)
    final = client.post(
        f"{ROOT}/query", json={"kind": "worker", "lifecycle": "finalized", "reference": targets[0]}
    ).json()["items"]
    assert len(final) == 1 and final[0]["complete"] and final[0]["display_name"] == name


@pytest.mark.parametrize("denial", ["worker:read", "worker_contact:read", "scope"])
def test_linked_worker_unavailable_metadata_never_matches_or_reveals_canonical_name(
    client, migration_database, denial
):
    refs = canonical(client)
    target = command(
        client, ROOT, {"kind": "worker", "content": {"phone": "202-555-0199"}}, 201
    ).json()["current"]["summary"]["intake_id"]
    link(migration_database, target, 1, reference(refs["worker"]))
    name = client.get(f"{ROOT}/{target}").json()["summary"]["display_name"]
    principal = (
        replace(LINKER, worker_scope=frozenset())
        if denial == "scope"
        else replace(LINKER, permissions=LINKER.permissions - {denial})
    )
    client.app.dependency_overrides[get_staff_principal] = lambda: principal
    response = client.post(f"{ROOT}/query", json={"kind": "worker", "reference": target})
    assert response.status_code == 200, response.text
    item = response.json()["items"][0]
    assert item["complete"] is None and item["missing_fields"] == []
    assert "display_name" not in item and name not in response.text
    assert (
        client.post(f"{ROOT}/query", json={"kind": "worker", "name_query": name}).json()["items"]
        == []
    )


@pytest.mark.parametrize("kind", ["household", "business"])
def test_linked_employer_list_uses_current_name_and_requires_selected_child_reads(
    client, migration_database, kind
):
    refs = canonical(client, kind)
    target = draft_employer(client, kind)
    link(
        migration_database,
        target,
        1,
        reference(refs["employer"]),
        contact=reference(refs["contact"]),
        worksite=reference(refs["worksite"]),
        business_address=reference(refs["business_address"]) if refs["business_address"] else None,
    )
    expected = client.get(f"{ROOT}/{target}").json()["summary"]
    query = {"kind": "employer", "reference": target}
    actual = client.post(f"{ROOT}/query", json=query).json()["items"][0]
    assert actual == expected
    matched = client.post(
        f"{ROOT}/query", json={"kind": "employer", "name_query": expected["display_name"]}
    )
    assert matched.status_code == 200, matched.text
    assert [item["intake_id"] for item in matched.json()["items"]] == [target]
    assert (
        client.post(
            f"{ROOT}/query", json={"kind": "employer", "name_query": "Candidate Preserved"}
        ).json()["items"]
        == []
    )
    for permission in [
        "employer:read",
        "employer_contact:read",
        "employer_contact:details:read",
        "worksite:read",
    ]:
        client.app.dependency_overrides[get_staff_principal] = lambda p=permission: replace(
            LINKER, permissions=LINKER.permissions - {p}
        )
        item = client.post(f"{ROOT}/query", json=query).json()["items"][0]
        assert item["complete"] is None and "display_name" not in item
        assert (
            client.post(
                f"{ROOT}/query", json={"kind": "employer", "name_query": expected["display_name"]}
            ).json()["items"]
            == []
        )
