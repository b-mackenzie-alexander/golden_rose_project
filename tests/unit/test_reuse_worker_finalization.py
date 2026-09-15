from dataclasses import replace
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import OperationalError

from golden_rose.application import finalize_intake as module
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.linked_intake_snapshot import LinkedSnapshot
from tests.unit.test_finalize_worker_command import command as command


@pytest.fixture
def reuse(command, monkeypatch):
    args, mocks = command
    row = mocks["get_intake"].return_value
    row["_has_link_row"] = True
    row["content"] = {"full_name": "Different candidate"}
    refs = {
        name: {"id": str(identity), "version": 2}
        for name, identity in mocks["insert_worker_group"].return_value.items()
    }
    args["principal"] = replace(
        args["principal"],
        permissions=(args["principal"].permissions | {"worker:read", "worker_contact:read"})
        - {"worker_residence:write"},
    )
    for name, value in {
        "review_dependencies": refs,
        "read_linked_snapshot": LinkedSnapshot(
            {"full_name": "Canonical"},
            {"worker_residence": {"line1": "Canonical street"}},
            refs,
            False,
        ),
    }.items():
        mocks[name] = Mock(return_value=value)
        monkeypatch.setattr(module, name, mocks[name])
    return args, mocks, refs


def test_reuse_emits_only_intake_authority_and_preserves_original_refs(reuse):
    args, mocks, refs = reuse
    result, replayed = module.execute_new_intake_finalization(**args)
    assert not replayed
    mocks["insert_worker_group"].assert_not_called()
    mocks["write_result_authority"].assert_not_called()
    mocks["get_address"].assert_not_called()
    mocks["write_authority"].assert_called_once()
    check = mocks["require_finalization_review"].call_args.kwargs
    assert check["dependency_refs"] == refs
    assert check["row"]["content"] == {"full_name": "Canonical"}
    assert mocks["get_intake"].return_value["content"] == {"full_name": "Different candidate"}
    for name in ("worker", "contact", "residence", "preferences"):
        assert result["finalization"][name]["disposition"] == "reused"
        assert result["finalization"][name]["version"] == 2
    statements = [call.args[0] for call in args["session"].execute.call_args_list]
    assert [statement.table.name for statement in statements] == ["intakes", "intake_finalizations"]
    args["session"].commit.assert_called_once()


@pytest.mark.parametrize("failure", ["stale", "incomplete", "storage"])
def test_reuse_never_creates_replacement_children_on_failure(reuse, failure):
    args, mocks, refs = reuse
    if failure == "stale":
        mocks["read_linked_snapshot"].return_value = LinkedSnapshot({}, {}, refs, True)
    elif failure == "incomplete":
        mocks["missing_fields"].return_value = ["phone"]
    else:
        args["session"].commit.side_effect = OperationalError("private", {}, Exception("private"))
    with pytest.raises(IntakeError) as error:
        module.execute_new_intake_finalization(**args)
    assert (
        error.value.code
        == {
            "stale": "dependency_changed",
            "incomplete": "canonical_incomplete",
            "storage": "persistence_unavailable",
        }[failure]
    )
    mocks["insert_worker_group"].assert_not_called()
    mocks["write_result_authority"].assert_not_called()
    args["session"].rollback.assert_called_once()


def test_reuse_replay_returns_original_refs_without_reresolving_current_versions(
    reuse, monkeypatch
):
    args, mocks, refs = reuse
    finalized = {
        "command_id": args["command_id"],
        "review_id": args["request"].review_id,
        "actor_id": args["principal"].actor_id,
        "result_version": 3,
        "kind": "worker",
    }
    from uuid import UUID

    for name, reference in refs.items():
        finalized.update(
            {
                f"{name}_id": UUID(reference["id"]),
                f"{name}_version": reference["version"],
                f"{name}_disposition": "reused",
            }
        )
    monkeypatch.setattr(module, "get_finalization", Mock(return_value=finalized))
    mocks["begin_command"].return_value = (
        b"x" * 32,
        {"result_entity_id": args["intake_id"], "result_record_version": 3},
    )
    mocks["get_intake"].return_value.update(version=4, lifecycle_status="finalized")
    args["session"].scalar.return_value = 1
    result, replayed = module.execute_new_intake_finalization(**args)
    assert replayed and result["result_record_version"] == 3
    mocks["read_linked_snapshot"].assert_not_called()
    mocks["insert_worker_group"].assert_not_called()
    args["session"].commit.assert_not_called()
    args["session"].rollback.assert_called_once()
