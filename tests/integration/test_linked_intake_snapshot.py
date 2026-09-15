"""Canonical snapshots from committed outputs without opening link storage."""

from copy import deepcopy
from dataclasses import replace
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from golden_rose.api.dependencies import get_staff_principal
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.linked_intake_snapshot import read_linked_snapshot
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.models import audit_events, command_receipts
from tests.integration.api.test_contact_details import canonical
from tests.integration.api.test_intake_finalizations import client as client
from tests.integration.api.test_intake_finalizations import reviewed_worker
from tests.integration.api.test_intake_review_workflows import ROOT, command


def dependencies(refs) -> dict[str, Any]:
    mapping = (
        {
            "worker": "worker",
            "contact": "worker_contact",
            "residence": "worker_residence",
            "preferences": "worker_preferences",
        }
        if refs["kind"] == "worker"
        else {
            "employer": "employer",
            "contact": "employer_contact",
            "contact_details": "employer_contact_details",
            "worksite": "worksite",
            "business_address": "employer_address",
        }
    )
    return {
        name: {"id": refs[key]["id"], "version": refs[key]["version"]}
        for key, name in mapping.items()
        if refs[key] is not None
    }


def reader(client) -> StaffPrincipal:
    principal: StaffPrincipal = client.app.dependency_overrides[get_staff_principal]()
    return replace(
        principal,
        permissions=principal.permissions
        | {"worker:read", "worker_contact:read", "employer_contact:details:read", "worksite:read"},
    )


@pytest.mark.parametrize("kind", ["worker", "household", "business"])
def test_canonical_snapshot_without_history_mutation(client, session, kind):
    if kind == "worker":
        target, body = reviewed_worker(client)
        refs = command(client, f"{ROOT}/{target}/finalizations", body, 201).json()["finalization"]
    else:
        _, refs, _ = canonical(client, kind)
    expected = dependencies(refs)
    before = [
        session.scalar(select(func.count()).select_from(t))
        for t in (audit_events, command_receipts)
    ]
    result = read_linked_snapshot(
        session=session, principal=reader(client), kind=refs["kind"], dependencies=expected
    )
    assert result.current_dependencies == expected
    assert not result.dependency_stale
    assert result.content["phone"] == "202-555-0151"
    assert set(result.addresses) == (
        {"worker_residence"} if kind == "worker" else {"party_address", "worksite_address"}
    )
    assert not {"residential_address", "party_address", "worksite_address"} & set(result.content)
    assert before == [
        session.scalar(select(func.count()).select_from(t))
        for t in (audit_events, command_receipts)
    ]


def test_legacy_employer_revision_marks_snapshot_stale_without_refreshing_expected(client, session):
    _, refs, principal = canonical(client, "business")
    expected = dependencies(refs)
    original = deepcopy(expected)
    principal = replace(principal, permissions=principal.permissions | {"employer:draft:revise"})
    client.app.dependency_overrides[get_staff_principal] = lambda: principal
    response = client.post(
        f"/api/staff/v1/employers/{refs['employer']['id']}/revisions",
        json={
            "expected_version": 1,
            "employer_type": "business",
            "display_name": "Fictional Revised Canonical",
        },
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 200, response.text
    result = read_linked_snapshot(
        session=session, principal=reader(client), kind="employer", dependencies=expected
    )
    assert result.dependency_stale
    assert result.content["display_name"] == "Fictional Revised Canonical"
    assert result.current_dependencies["employer"]["version"] == 2
    assert expected == original


def test_snapshot_rejects_cross_employer_selected_child(client, session):
    _, first, _ = canonical(client, "business")
    _, second, _ = canonical(client, "business")
    expected = dependencies(first)
    expected["worksite"] = dependencies(second)["worksite"]
    with pytest.raises(IntakeError) as error:
        read_linked_snapshot(
            session=session, principal=reader(client), kind="employer", dependencies=expected
        )
    assert error.value.status == 404
