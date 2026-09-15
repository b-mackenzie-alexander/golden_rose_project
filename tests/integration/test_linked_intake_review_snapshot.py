"""Effective review facts from real outputs while durable link writes remain closed."""

from copy import deepcopy
from uuid import UUID

import pytest
from sqlalchemy import func, select

from golden_rose.application.intake_review_snapshot import build_review_snapshot
from golden_rose.persistence.intakes import get_intake, missing_fields
from golden_rose.persistence.models import audit_events, command_receipts
from tests.integration.api.test_contact_details import canonical
from tests.integration.api.test_intake_finalizations import client as client
from tests.integration.api.test_intake_finalizations import reviewed_worker
from tests.integration.api.test_intake_review_workflows import ROOT, command
from tests.integration.test_linked_intake_snapshot import dependencies, reader
from tests.unit.test_employer_finalization_outputs import content


@pytest.mark.parametrize("kind", ["worker", "household", "business"])
def test_effective_review_uses_real_selected_facts_not_candidate_overrides(client, session, kind):
    if kind == "worker":
        target, body = reviewed_worker(client)
        refs = command(client, f"{ROOT}/{target}/finalizations", body, 201).json()["finalization"]
        candidate = {"full_name": "Different candidate"}
    else:
        _, refs, _ = canonical(client, kind)
        candidate = {
            **content(kind),
            "display_name": "Different candidate",
            "representative_name": "Different candidate contact",
            "phone": "202-555-0199",
            "role_title": "New fictional request",
        }
    draft = command(client, ROOT, {"kind": refs["kind"], "content": candidate}, 201).json()[
        "current"
    ]
    row = get_intake(session, UUID(draft["summary"]["intake_id"]), lock=True)
    original = deepcopy(row)
    before = [
        session.scalar(select(func.count()).select_from(t))
        for t in (audit_events, command_receipts)
    ]
    snapshot = build_review_snapshot(session, reader(client), row, dependencies(refs))
    assert snapshot["content"]["phone"] == "202-555-0151"
    assert "Different candidate" not in str(snapshot)
    assert not missing_fields(
        session, {**row, "content": snapshot["content"]}, addresses=snapshot["addresses"]
    )
    if kind != "worker":
        assert snapshot["content"]["role_title"] == "New fictional request"
    assert row == original
    assert before == [
        session.scalar(select(func.count()).select_from(t))
        for t in (audit_events, command_receipts)
    ]
