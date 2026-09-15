from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from golden_rose.api.staff.intake_schemas import WorkerFinalizationOutputs


def outputs(disposition="reused", version=3) -> dict[str, Any]:
    return {
        "kind": "worker",
        **{
            name: {"id": str(uuid4()), "version": version, "disposition": disposition}
            for name in ("worker", "contact", "residence", "preferences")
        },
    }


def test_reused_outputs_keep_original_versions():
    payload = outputs()
    assert WorkerFinalizationOutputs.model_validate(payload).model_dump(mode="json") == payload


def test_created_outputs_still_require_version_one():
    with pytest.raises(ValidationError):
        WorkerFinalizationOutputs.model_validate(outputs("created", 2))
    WorkerFinalizationOutputs.model_validate(outputs("created", 1))


@pytest.mark.parametrize("name", ["worker", "contact", "residence", "preferences"])
def test_partial_worker_reuse_is_rejected(name):
    payload = outputs()
    payload[name].update(disposition="created", version=1)
    with pytest.raises(ValidationError):
        WorkerFinalizationOutputs.model_validate(payload)
