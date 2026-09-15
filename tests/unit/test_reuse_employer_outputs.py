from itertools import product
from typing import Any
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from golden_rose.api.staff.intake_schemas import EmployerFinalizationOutputs
from golden_rose.persistence.employer_intake_outputs import insert_employer_group
from tests.unit.test_employer_finalization_outputs import ACTOR, NOW, PARTY, WORKSITE, content


@pytest.mark.parametrize(
    "kind,contact,worksite,address",
    [
        (kind, contact, worksite, address)
        for kind in ("household", "business")
        for contact, worksite, address in product((False, True), repeat=3)
        if kind == "business" or not address
    ],
)
def test_only_unselected_records_and_one_request_are_created(kind, contact, worksite, address):
    names = {"employer"}
    if contact:
        names.update({"employer_contact", "employer_contact_details"})
    if worksite:
        names.add("worksite")
    if address:
        names.add("employer_address")
    refs = {name: {"id": str(uuid4()), "version": 2} for name in names}
    session = Mock()
    created = insert_employer_group(
        session,
        content=content(kind),
        party_address=PARTY,
        worksite_address=WORKSITE,
        actor_id=ACTOR,
        now=NOW,
        reused=refs,
    )
    expected = {"employer_contact", "employer_contact_details", "worksite", "staffing_request"}
    if kind == "business":
        expected.add("employer_address")
    assert set(created) == expected - names
    rows = [
        (call.args[0].table.name, call.args[0].compile().params)
        for call in session.execute.call_args_list
    ]
    assert all(call.args[0].is_insert for call in session.execute.call_args_list)
    assert "employers" not in {name for name, _ in rows}
    for entity, table in (
        ("employer_contact", "employer_contacts"),
        ("employer_contact_details", "employer_contact_details"),
        ("worksite", "worksites"),
        ("employer_address", "employer_addresses"),
    ):
        assert (table in {name for name, _ in rows}) == (entity in created)
    requests = [row for table, row in rows if table == "staffing_requests"]
    assert len(requests) == 1
    request = requests[0]
    for entity in ("employer", "employer_contact", "worksite"):
        assert request[f"{entity}_id"] == (
            UUID(str(refs[entity]["id"])) if entity in refs else created[entity]
        )
    assert request["request_status"] == "draft"
    assert len([row for table, row in rows if table == "entity_authorities"]) == len(created)
    session.commit.assert_not_called()


def output() -> dict[str, Any]:
    def ref(disposition) -> dict[str, Any]:
        return {"id": str(uuid4()), "version": 1, "disposition": disposition}

    return {
        "kind": "employer",
        "employer": ref("reused"),
        "contact": ref("reused"),
        "contact_details": ref("reused"),
        "worksite": ref("created"),
        "request": ref("created"),
        "business_address": None,
    }


def test_mixed_employer_outputs_are_valid_with_one_new_request():
    EmployerFinalizationOutputs.model_validate(output())


@pytest.mark.parametrize("change", ["request", "contact_pair", "parent"])
def test_output_shape_rejects_invalid_reuse(change):
    value = output()
    if change == "request":
        value["request"]["disposition"] = "reused"
    elif change == "contact_pair":
        value["contact_details"]["disposition"] = "created"
    else:
        value["employer"]["disposition"] = "created"
    with pytest.raises(ValidationError):
        EmployerFinalizationOutputs.model_validate(value)
