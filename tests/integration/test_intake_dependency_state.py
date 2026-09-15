"""Version-only freshness probes against real canonical outputs."""

from copy import deepcopy

import pytest

from golden_rose.persistence.intake_dependency_state import dependencies_current
from tests.integration.api.test_contact_details import canonical
from tests.integration.api.test_intake_finalizations import client as client
from tests.integration.api.test_intake_finalizations import reviewed_worker
from tests.integration.api.test_intake_review_workflows import ROOT, command
from tests.integration.test_linked_intake_snapshot import dependencies


@pytest.mark.parametrize("kind", ["worker", "household", "business"])
def test_current_and_changed_expected_versions(client, session, kind):
    if kind == "worker":
        target, body = reviewed_worker(client)
        outputs = command(client, f"{ROOT}/{target}/finalizations", body, 201).json()[
            "finalization"
        ]
    else:
        _, outputs, _ = canonical(client, kind)
    references = dependencies(outputs)
    original = deepcopy(references)
    assert dependencies_current(session, outputs["kind"], references)
    for name in references:
        changed = deepcopy(references)
        changed[name]["version"] += 1
        assert not dependencies_current(session, outputs["kind"], changed)
    assert references == original


def test_cross_parent_child_is_not_current(client, session):
    _, first, _ = canonical(client, "business")
    _, second, _ = canonical(client, "business")
    references = dependencies(first)
    references["worksite"] = dependencies(second)["worksite"]
    assert not dependencies_current(session, "employer", references)
