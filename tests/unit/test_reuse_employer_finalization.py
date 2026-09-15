from dataclasses import replace
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import OperationalError

from golden_rose.application import finalize_intake as module
from golden_rose.application.intake_errors import IntakeError
from tests.unit.test_employer_finalization_outputs import PARTY, WORKSITE, content
from tests.unit.test_finalize_worker_command import command as command


@pytest.fixture
def reuse(command, monkeypatch):
    args, mocks = command
    row = mocks["get_intake"].return_value
    row.update(kind="employer", content={"display_name": "Different candidate"}, _has_link_row=True)
    refs = {
        name: {"id": str(uuid4()), "version": 2}
        for name in (
            "employer",
            "employer_contact",
            "employer_contact_details",
            "employer_address",
            "worksite",
        )
    }
    args["principal"] = replace(
        args["principal"],
        permissions=frozenset(
            {
                "intake:read",
                "intake:finalize",
                "employer:read",
                "employer_contact:read",
                "employer_contact:details:read",
                "party_address:read",
                "worksite:read",
                "worksite_address:read",
            }
        ),
    )
    args["session"].scalar.return_value = "business"
    for name, value in {
        "review_dependencies": refs,
        "build_review_snapshot": {
            "kind": "employer",
            "content": content("business"),
            "addresses": {"party_address": PARTY, "worksite_address": WORKSITE},
        },
        "insert_employer_group": {"staffing_request": uuid4()},
    }.items():
        mocks[name] = Mock(return_value=value)
        monkeypatch.setattr(module, name, mocks[name])
    return args, mocks, refs


def test_all_selected_employer_creates_only_request_and_intake_events(reuse):
    args, mocks, refs = reuse
    result, replayed = module.execute_new_intake_finalization(**args)
    assert not replayed
    assert mocks["insert_employer_group"].call_args.kwargs["reused"] == refs
    assert mocks["insert_employer_group"].call_args.kwargs["content"] == content("business")
    assert mocks["require_finalization_review"].call_args.kwargs["dependency_refs"] == refs
    assert mocks["get_intake"].return_value["content"] == {"display_name": "Different candidate"}
    mocks["insert_worker_group"].assert_not_called()
    mocks["get_address"].assert_not_called()
    mocks["write_result_authority"].assert_called_once()
    assert mocks["write_result_authority"].call_args.kwargs["entity_type"] == "staffing_request"
    for name, ref in result["finalization"].items():
        if isinstance(ref, dict):
            assert ref["disposition"] == ("created" if name == "request" else "reused")
    args["session"].commit.assert_called_once()


@pytest.mark.parametrize(
    "missing,code", [("phone", "canonical_incomplete"), ("role_title", "incomplete")]
)
def test_selected_and_new_fields_keep_distinct_incompleteness(reuse, missing, code):
    args, mocks, _ = reuse
    mocks["missing_fields"].return_value = [missing]
    with pytest.raises(IntakeError) as error:
        module.execute_new_intake_finalization(**args)
    assert error.value.code == code
    mocks["insert_employer_group"].assert_not_called()
    args["session"].rollback.assert_called_once()


def test_new_address_still_requires_write_permission(reuse):
    args, mocks, refs = reuse
    del refs["employer_address"]
    with pytest.raises(IntakeError) as error:
        module.execute_new_intake_finalization(**args)
    assert error.value.status == 403
    mocks["begin_command"].assert_not_called()


def test_household_contact_address_reuse_needs_no_address_write(reuse):
    args, mocks, refs = reuse
    del refs["employer_address"]
    args["session"].scalar.return_value = "household"
    mocks["build_review_snapshot"].return_value["content"] = content("household")
    result, replayed = module.execute_new_intake_finalization(**args)
    assert not replayed and result["finalization"]["business_address"] is None
    assert result["finalization"]["contact_details"]["disposition"] == "reused"
    args["session"].commit.assert_called_once()


def test_partial_reuse_emits_events_for_new_worksite_and_request_only(reuse):
    args, mocks, refs = reuse
    del refs["worksite"]
    args["principal"] = replace(
        args["principal"], permissions=args["principal"].permissions | {"worksite_address:write"}
    )
    mocks["insert_employer_group"].return_value["worksite"] = uuid4()
    result, _ = module.execute_new_intake_finalization(**args)
    assert {
        call.kwargs["entity_type"] for call in mocks["write_result_authority"].call_args_list
    } == {"worksite", "staffing_request"}
    assert result["finalization"]["worksite"]["disposition"] == "created"
    assert result["finalization"]["contact"]["disposition"] == "reused"


def test_canonical_type_recheck_cannot_bypass_new_address_write_permission(reuse):
    args, mocks, refs = reuse
    del refs["employer_address"]
    args["session"].scalar.side_effect = ["household", "household", "business"]
    with pytest.raises(IntakeError) as error:
        module.execute_new_intake_finalization(**args)
    assert error.value.status == 403
    mocks["insert_employer_group"].assert_not_called()
    args["session"].rollback.assert_called_once()


@pytest.mark.parametrize("stage", ["insert_employer_group", "write_result_authority", "commit"])
def test_late_failure_rolls_back_the_outer_employer_command(reuse, stage):
    args, mocks, _ = reuse
    target = args["session"].commit if stage == "commit" else mocks[stage]
    target.side_effect = OperationalError("private", {}, Exception("private"))
    with pytest.raises(IntakeError) as error:
        module.execute_new_intake_finalization(**args)
    assert error.value.status == 503
    assert str(error.value) == "persistence_unavailable"
    args["session"].rollback.assert_called_once()


@pytest.mark.parametrize("result_count", [2, 7])
def test_replay_counts_only_created_outputs_and_keeps_original_refs(
    reuse, monkeypatch, result_count
):
    args, mocks, refs = reuse
    finalized = {
        "kind": "employer",
        "command_id": args["command_id"],
        "review_id": args["request"].review_id,
        "actor_id": args["principal"].actor_id,
        "result_version": 3,
    }
    for name, ref in refs.items():
        finalized.update(
            {
                f"{name}_id": UUID(ref["id"]),
                f"{name}_version": ref["version"],
                f"{name}_disposition": "reused",
            }
        )
    finalized.update(
        staffing_request_id=uuid4(),
        staffing_request_version=1,
        staffing_request_disposition="created",
    )
    monkeypatch.setattr(module, "get_finalization", Mock(return_value=finalized))
    mocks["get_intake"].return_value.update(version=4, lifecycle_status="finalized")
    mocks["begin_command"].return_value = (
        b"x" * 32,
        {"result_entity_id": args["intake_id"], "result_record_version": 3},
    )
    args["session"].scalar.side_effect = ["business", "business", result_count]
    if result_count == 2:
        result, replayed = module.execute_new_intake_finalization(**args)
        assert replayed and result["result_record_version"] == 3
        assert result["finalization"]["employer"]["version"] == 2
    else:
        with pytest.raises(IntakeError) as error:
            module.execute_new_intake_finalization(**args)
        assert error.value.status == 503
    mocks["build_review_snapshot"].assert_not_called()
    mocks["insert_employer_group"].assert_not_called()
    args["session"].rollback.assert_called_once()
