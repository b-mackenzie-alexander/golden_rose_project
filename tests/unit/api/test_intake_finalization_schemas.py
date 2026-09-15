from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from golden_rose.api.staff.intake_finalization_schemas import (
    FinalizeIntakeRequest,
    LinkIntakeRequest,
)


def test_finalization_accepts_only_saved_version_and_review_identity():
    review_id = uuid4()
    request = FinalizeIntakeRequest.model_validate(
        {"expected_version": 3, "review_id": str(review_id)}
    )
    assert request.review_id == review_id
    assert request.model_dump(mode="json") == {
        "expected_version": 3,
        "review_id": str(review_id),
    }


@pytest.mark.parametrize(
    "patch",
    [
        {"expected_version": True},
        {"expected_version": "3"},
        {"expected_version": 3.0},
        {"expected_version": 0},
        {"expected_version": 2147483647},
        {"review_id": None},
        {"review_id": "invalid"},
        {"review_id": uuid4().hex},
        {"content": {}},
        {"actor_id": str(uuid4())},
        {"command_id": str(uuid4())},
        {"occurred_at": "2026-09-14T12:00:00Z"},
    ],
)
def test_finalization_rejects_coercion_and_unreviewed_values(patch):
    with pytest.raises(ValidationError):
        FinalizeIntakeRequest.model_validate(
            {"expected_version": 3, "review_id": str(uuid4()), **patch}
        )


def test_links_preserve_explicit_null_versus_omitted_child_choices():
    party = {"id": str(uuid4()), "version": 2}
    omitted = LinkIntakeRequest.model_validate({"expected_version": 4, "party": party})
    explicit = LinkIntakeRequest.model_validate(
        {"expected_version": 4, "party": party, "contact": None}
    )
    assert "contact" not in omitted.model_dump(mode="json", exclude_unset=True)
    assert explicit.model_dump(mode="json", exclude_unset=True)["contact"] is None
    assert omitted.party is not None
    assert omitted.party.id == UUID(str(party["id"]))


def test_link_requires_explicit_party_selection_or_unlink():
    with pytest.raises(ValidationError):
        LinkIntakeRequest.model_validate({"expected_version": 1})
    request = LinkIntakeRequest.model_validate({"expected_version": 1, "party": None})
    assert request.party is None


@pytest.mark.parametrize(
    "patch",
    [
        {"expected_version": True},
        {"expected_version": "1"},
        {"expected_version": 1.0},
        {"expected_version": 0},
        {"expected_version": 2147483647},
        {"actor_id": str(uuid4())},
        {"content": {}},
        {"worker_contact": {"id": str(uuid4()), "version": 1}},
    ],
)
def test_link_rejects_coercion_and_client_resolved_worker_children(patch):
    with pytest.raises(ValidationError):
        LinkIntakeRequest.model_validate({"expected_version": 1, "party": None, **patch})


def test_link_accepts_versioned_employer_choices_and_explicit_dependent_unlinks():
    body = {
        "expected_version": 2147483646,
        **{
            field: {"id": str(uuid4()), "version": 2147483647}
            for field in ("party", "contact", "worksite", "business_address")
        },
    }
    assert LinkIntakeRequest.model_validate(body).model_dump(mode="json") == body
    unlinked = {
        "expected_version": 2,
        "party": None,
        "contact": None,
        "worksite": None,
        "business_address": None,
    }
    assert LinkIntakeRequest.model_validate(unlinked).model_dump(mode="json") == unlinked


@pytest.mark.parametrize("child", ["contact", "worksite", "business_address"])
def test_sublinks_require_a_party(child):
    with pytest.raises(ValidationError):
        LinkIntakeRequest.model_validate(
            {"expected_version": 1, "party": None, child: {"id": str(uuid4()), "version": 1}}
        )


@pytest.mark.parametrize("field", ["party", "contact", "worksite", "business_address"])
@pytest.mark.parametrize(
    "patch",
    [
        {"id": "invalid"},
        {"id": uuid4().hex},
        {"id": 123},
        {"version": True},
        {"version": "1"},
        {"version": 0},
        {"version": 2147483648},
        {"address": {"line1": "Fictional address"}},
        {"full_name": "Fictional name"},
        {"disposition": "created"},
    ],
)
def test_link_references_reject_values_and_recursive_extra_fields(field, patch):
    with pytest.raises(ValidationError):
        LinkIntakeRequest.model_validate(
            {
                "expected_version": 1,
                "party": {"id": str(uuid4()), "version": 1},
                field: {"id": str(uuid4()), "version": 1, **patch},
            }
        )


def output_refs() -> dict[str, Any]:
    return {
        "kind": "worker",
        **{
            name: {"id": str(uuid4()), "version": 1, "disposition": "created"}
            for name in ("worker", "contact", "residence", "preferences")
        },
    }


def test_finalized_detail_and_command_preserve_exact_output_refs():
    from golden_rose.api.staff.intake_schemas import IntakeCommandResponse, IntakeDetail
    from tests.unit.api.test_intake_schemas import response_detail

    detail = response_detail()
    detail["summary"].update(lifecycle="finalized", version=3)
    detail["finalization"] = output_refs()
    assert IntakeDetail.model_validate(detail).finalization is not None
    command = {
        "command_id": str(uuid4()),
        "result_record_version": 3,
        "current": detail,
        "finalization": detail["finalization"],
    }
    IntakeCommandResponse.model_validate(command)
    command["finalization"] = output_refs()
    with pytest.raises(ValidationError):
        IntakeCommandResponse.model_validate(command)


@pytest.mark.parametrize(
    "patch",
    [
        {"version": True},
        {"version": "1"},
        {"version": 2},
        {"disposition": "reused"},
        {"phone": "+12025550123"},
        {"address": {"line1": "Fictional"}},
    ],
)
def test_created_worker_output_refs_are_strict_and_value_free(patch):
    from golden_rose.api.staff.intake_schemas import WorkerFinalizationOutputs

    refs = output_refs()
    refs["worker"].update(patch)
    with pytest.raises(ValidationError):
        WorkerFinalizationOutputs.model_validate(refs)


@pytest.mark.parametrize("lifecycle,with_outputs", [("draft", True), ("finalized", False)])
def test_finalization_output_presence_matches_lifecycle(lifecycle, with_outputs):
    from golden_rose.api.staff.intake_schemas import IntakeDetail
    from tests.unit.api.test_intake_schemas import response_detail

    detail = response_detail()
    detail["summary"]["lifecycle"] = lifecycle
    if with_outputs:
        detail["finalization"] = output_refs()
    with pytest.raises(ValidationError):
        IntakeDetail.model_validate(detail)


@pytest.mark.parametrize("business", [False, True])
def test_employer_finalization_response_preserves_typed_outputs(business):
    from golden_rose.api.staff.intake_schemas import IntakeCommandResponse
    from tests.unit.api.test_intake_schemas import response_detail

    ref = output_refs()["worker"]
    outputs = {
        "kind": "employer",
        **{
            field: {**ref, "id": str(uuid4())}
            for field in ("employer", "contact", "contact_details", "worksite", "request")
        },
        "business_address": {**ref, "id": str(uuid4())} if business else None,
    }
    detail = response_detail()
    detail["summary"].update(kind="employer", lifecycle="finalized", version=3)
    detail["candidate"] = {
        "employer_type": "business" if business else "household",
        "display_name": "Fictional Employer",
    }
    detail["finalization"] = outputs
    response = IntakeCommandResponse.model_validate(
        {
            "command_id": str(uuid4()),
            "result_record_version": 3,
            "current": detail,
            "finalization": outputs,
        }
    )
    assert response.model_dump(mode="json")["finalization"] == outputs
