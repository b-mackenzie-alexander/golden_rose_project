from dataclasses import replace
from typing import Any
from uuid import UUID, uuid4

from golden_rose.api.staff.canonical_correction_schemas import ReviewCanonicalOutputsRequest
from golden_rose.application.review_canonical_outputs import (
    execute_current_review,
    read_current_review,
)
from tests.integration.test_canonical_corrections import CORRECTOR, corrected
from tests.integration.test_intake_commands import Clock
from tests.integration.test_intake_finalization import draft as draft
from tests.integration.test_intake_finalization import finalize, review

REVIEWER = replace(CORRECTOR, permissions=CORRECTOR.permissions | {"canonical:review"})


def test_correction_stales_current_review_and_rereview_binds_all_current_versions(session, draft):
    result, _ = finalize(session, draft, review(session, draft, 1))
    state = read_current_review(session=session, principal=REVIEWER, intake_id=draft)
    assert state["status"] == "unreviewed"

    def rereview(state: dict[str, Any]) -> dict[str, Any]:
        result = execute_current_review(
            session=session,
            principal=REVIEWER,
            intake_id=draft,
            command_id=uuid4(),
            request=ReviewCanonicalOutputsRequest.model_validate(
                {
                    "expected_review_version": state["review_version"],
                    "expected_versions": state["dependencies"],
                }
            ),
            clock=Clock(),
        )[0]["current"]
        assert isinstance(result, dict)
        return result

    assert rereview(state)["status"] == "current"
    corrected(session, UUID(result["finalization"]["worker"]["id"]))
    state = read_current_review(session=session, principal=REVIEWER, intake_id=draft)
    assert state["status"] == "stale"
    assert state["dependencies"]["worker"]["version"] == 2
    assert rereview(state)["review_version"] == 2
