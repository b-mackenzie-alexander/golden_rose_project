"""Current dependencies advance without weakening immutable finalization DTOs."""

from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from golden_rose.api.staff.canonical_correction_schemas import (
    CanonicalCorrectionResponse,
    CanonicalReviewState,
    ReviewCanonicalOutputsRequest,
)
from golden_rose.api.staff.intake_schemas import WorkerFinalizationOutputs


def dependencies() -> dict[str, Any]:
    return {
        "kind": "worker",
        **{
            key: {"id": str(uuid4()), "version": 2, "disposition": "created"}
            for key in ("worker", "contact", "residence", "preferences")
        },
    }


def test_current_versions_may_advance_but_original_outputs_must_not():
    values = dependencies()
    parsed = ReviewCanonicalOutputsRequest.model_validate(
        {"expected_review_version": 0, "expected_versions": values}
    ).expected_versions
    assert parsed.kind == "worker"
    assert parsed.worker.version == 2
    with pytest.raises(ValidationError):
        WorkerFinalizationOutputs.model_validate(values)


@pytest.mark.parametrize(
    "patch",
    [
        {"expected_review_version": True},
        {"expected_review_version": -1},
        {"expected_review_version": 2147483647},
        {"note": " "},
    ],
)
def test_review_rejects_invalid_versions_and_note(patch):
    with pytest.raises(ValidationError):
        ReviewCanonicalOutputsRequest.model_validate(
            {"expected_review_version": 0, "expected_versions": dependencies(), **patch}
        )


def test_current_review_state_requires_consistent_head():
    body = {
        "review_version": 0,
        "latest_review_id": None,
        "status": "unreviewed",
        "dependencies": dependencies(),
    }
    assert CanonicalReviewState.model_validate(body).review_version == 0
    for patch in ({"status": "current"}, {"review_version": 1}, {"latest_review_id": str(uuid4())}):
        with pytest.raises(ValidationError):
            CanonicalReviewState.model_validate({**body, **patch})


def test_correction_response_cannot_claim_future_saved_version():
    body = {
        "command_id": str(uuid4()),
        "result_record_version": 2,
        "event_id": str(uuid4()),
        "target": {"entity_type": "worker", "id": str(uuid4()), "current_version": 2},
    }
    assert CanonicalCorrectionResponse.model_validate(body).result_record_version == 2
    body["result_record_version"] = 3
    with pytest.raises(ValidationError):
        CanonicalCorrectionResponse.model_validate(body)
