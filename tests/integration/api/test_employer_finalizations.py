"""Real PostgreSQL new household/business finalization and legacy compatibility."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from golden_rose.api.dependencies import get_staff_principal
from golden_rose.application import finalize_intake
from golden_rose.application.intake_workflow_common import write_result_authority
from golden_rose.persistence.employer_intake_outputs import insert_new_employer_group
from golden_rose.persistence.models import (
    command_results,
    employer_addresses,
    employer_contact_details,
    employer_contacts,
    employers,
    intake_finalizations,
    staffing_requests,
    worksites,
)
from tests.integration.api.test_intake_finalizations import client as client
from tests.integration.api.test_intake_review_workflows import ROOT, command
from tests.unit.test_employer_finalization_outputs import PARTY, WORKSITE, content


def reviewed_employer(client: TestClient, kind: str = "household") -> tuple[str, dict[str, Any]]:
    candidate = {**content(kind), "party_address": PARTY, "worksite_address": WORKSITE}
    target = command(client, ROOT, {"kind": "employer", "content": candidate}, 201).json()[
        "current"
    ]["summary"]["intake_id"]
    review = command(
        client, f"{ROOT}/{target}/reviews", {"expected_version": 1, "outcome": "intake_reviewed"}
    ).json()["current"]
    return target, {"expected_version": 2, "review_id": review["latest_review"]["review_id"]}


@pytest.mark.parametrize("kind,count", [("household", 6), ("business", 7)])
def test_employer_atomic_finalization_replay_and_legacy_reads(client, session, kind, count):
    target, body = reviewed_employer(client, kind)
    key = uuid4()
    path = f"{ROOT}/{target}/finalizations"
    result = command(client, path, body, 201, key).json()
    refs = result["finalization"]
    assert refs["kind"] == "employer"
    assert result["current"]["summary"]["lifecycle"] == "finalized"
    assert result["current"]["content_version"] == 1
    assert (refs["business_address"] is not None) == (kind == "business")
    assert (
        session.scalar(
            select(func.count())
            .select_from(command_results)
            .where(command_results.c.command_id == key)
        )
        == count
    )
    details = session.execute(select(employer_contact_details)).mappings().one()
    assert details["phone"] == content(kind)["phone"]
    assert details["line1"] == (PARTY["line1"] if kind == "household" else None)
    request = session.execute(select(staffing_requests)).mappings().one()
    assert request["request_status"] == "draft"
    assert request["request_type"] == ("household" if kind == "household" else "general_labor")
    assert str(request["employer_id"]) == refs["employer"]["id"]
    assert str(request["employer_contact_id"]) == refs["contact"]["id"]
    assert str(request["worksite_id"]) == refs["worksite"]["id"]
    legacy = client.get(f"/api/staff/v1/employers/{refs['employer']['id']}")
    assert legacy.status_code == 200, legacy.text
    contact = client.get(
        f"/api/staff/v1/employers/{refs['employer']['id']}/contacts/{refs['contact']['id']}"
    )
    assert contact.status_code == 200, contact.text
    assert "phone" not in contact.json()
    assert PARTY["line1"] not in str(result) and WORKSITE["line1"] not in str(result)
    replay = command(client, path, body, key=key)
    assert replay.headers["idempotency-replayed"] == "true"
    assert replay.json()["finalization"] == refs
    assert client.get(f"{ROOT}/{target}").json()["finalization"] == refs
    assert command(client, path, body, 409).json()["code"] == "already_finalized"


@pytest.mark.parametrize(
    "permission",
    [
        "party_address:read",
        "party_address:write",
        "worksite_address:read",
        "worksite_address:write",
        "intake:finalize",
    ],
)
def test_employer_replay_requires_current_restricted_authority(client, permission):
    target, body = reviewed_employer(client)
    key = uuid4()
    path = f"{ROOT}/{target}/finalizations"
    command(client, path, body, 201, key)
    principal = client.app.dependency_overrides[get_staff_principal]()
    revoked = replace(principal, permissions=principal.permissions - {permission})
    client.app.dependency_overrides[get_staff_principal] = lambda: revoked
    assert command(client, path, body, 403, key).json()["code"] == "forbidden"


@pytest.mark.parametrize("failure", ["missing_result", "unreviewed_name"])
def test_employer_authority_failure_rolls_back_entire_group(client, session, monkeypatch, failure):
    target, body = reviewed_employer(client)
    if failure == "missing_result":
        original = write_result_authority

        def omit(session, **kwargs):
            if kwargs["entity_type"] != "worksite":
                original(session, **kwargs)

        monkeypatch.setattr(finalize_intake, "write_result_authority", omit)
    else:
        original_insert = insert_new_employer_group

        def changed(session, **kwargs):
            kwargs["content"] = {**kwargs["content"], "display_name": "Fictional Unreviewed Name"}
            return original_insert(session, **kwargs)

        monkeypatch.setattr(finalize_intake, "insert_new_employer_group", changed)
    response = command(client, f"{ROOT}/{target}/finalizations", body, 503)
    assert response.json()["code"] == "persistence_unavailable"
    for table in (
        employers,
        employer_contacts,
        employer_contact_details,
        employer_addresses,
        worksites,
        staffing_requests,
        intake_finalizations,
    ):
        assert session.scalar(select(func.count()).select_from(table)) == 0
    assert client.get(f"{ROOT}/{target}").json()["summary"]["lifecycle"] == "draft"


@pytest.mark.parametrize("same_key", [True, False])
def test_employer_finalization_race_creates_one_request(client, session, same_key):
    target, body = reviewed_employer(client, "business")
    first = uuid4()
    keys = [first, first if same_key else uuid4()]
    ready = Barrier(2)

    def submit(key):
        ready.wait(timeout=10)
        return client.post(
            f"{ROOT}/{target}/finalizations", json=body, headers={"Idempotency-Key": str(key)}
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(submit, keys))
    assert sorted(response.status_code for response in responses) == (
        [200, 201] if same_key else [201, 409]
    )
    assert session.scalar(select(func.count()).select_from(staffing_requests)) == 1
    if same_key:
        assert responses[0].json()["finalization"] == responses[1].json()["finalization"]
