from dataclasses import replace
from uuid import uuid4

import pytest

from golden_rose.api.dependencies import get_staff_principal
from tests.integration.api.test_employer_finalizations import reviewed_employer
from tests.integration.api.test_intake_finalizations import client as client
from tests.integration.api.test_intake_finalizations import reviewed_worker
from tests.integration.api.test_intake_review_workflows import ROOT, command
from tests.integration.test_canonical_corrections import CORRECTOR


@pytest.mark.parametrize("kind", ["worker", "household", "business"])
def test_current_review_is_separate_and_exactly_replayable(client, kind):
    intake_id, body = (
        reviewed_worker(client) if kind == "worker" else reviewed_employer(client, kind)
    )
    original = command(client, f"{ROOT}/{intake_id}/finalizations", body, 201).json()
    reviewer = replace(
        CORRECTOR,
        permissions=CORRECTOR.permissions | {"canonical:review", "intake:restricted_history:read"},
    )
    client.app.dependency_overrides[get_staff_principal] = lambda: reviewer
    prefix = f"/api/staff/v1/intake-finalizations/{intake_id}"
    state = client.get(f"{prefix}/current-review")
    assert state.status_code == 200, state.text
    request = {
        "expected_review_version": 0,
        "expected_versions": state.json()["dependencies"],
        "note": "Fictional current-facts review",
    }
    key = uuid4()
    result = command(client, f"{prefix}/current-reviews", request, 201, key).json()
    assert result["current"]["status"] == "current"
    assert command(client, f"{prefix}/current-reviews", request, key=key).json() == result
    history = client.get(f"{prefix}/current-reviews/{result['review_id']}/restricted")
    assert history.status_code == 200, history.text
    assert history.json()["note"] == request["note"]
    assert client.get(f"{ROOT}/{intake_id}").json()["finalization"] == original["finalization"]
    changed = {
        **request,
        "expected_review_version": 1,
        "expected_versions": {**request["expected_versions"]},
    }
    section = "worker" if kind == "worker" else "request"
    changed["expected_versions"][section] = {**changed["expected_versions"][section], "version": 2}
    assert (
        command(client, f"{prefix}/current-reviews", changed, 409).json()["code"]
        == "dependency_changed"
    )


def test_reclassified_employer_does_not_repurpose_original_business_address(client, session):
    from uuid import UUID

    from golden_rose.application.revise_draft_employer import revise_draft_employer
    from tests.integration.test_intake_commands import Clock

    intake_id, body = reviewed_employer(client, "business")
    refs = command(client, f"{ROOT}/{intake_id}/finalizations", body, 201).json()["finalization"]
    reviewer = replace(
        CORRECTOR, permissions=CORRECTOR.permissions | {"canonical:review", "employer:draft:revise"}
    )
    client.app.dependency_overrides[get_staff_principal] = lambda: reviewer
    revise_draft_employer(
        session=session,
        principal=reviewer,
        command_id=uuid4(),
        employer_id=UUID(refs["employer"]["id"]),
        expected_version=1,
        employer_type="household",
        display_name="Fictional Reclassified",
        clock=Clock(),
    )
    prefix = f"/api/staff/v1/intake-finalizations/{intake_id}"
    state = client.get(prefix + "/current-review").json()
    result = command(
        client,
        prefix + "/current-reviews",
        {"expected_review_version": 0, "expected_versions": state["dependencies"]},
        422,
    )
    assert result.json()["code"] == "incomplete"
    assert client.get(f"{ROOT}/{intake_id}").json()["finalization"] == refs
