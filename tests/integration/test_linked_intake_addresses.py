"""HTTP projection against real outputs with injected, not persisted, link metadata."""

from dataclasses import replace
from typing import Any
from uuid import UUID

import pytest

from golden_rose.api.dependencies import get_staff_principal
from golden_rose.api.staff import intakes as routes
from golden_rose.application import read_linked_intake_address as reader_module
from golden_rose.persistence.intakes import get_intake
from tests.integration.api.test_contact_details import canonical
from tests.integration.api.test_intake_finalizations import client as client
from tests.integration.api.test_intake_finalizations import reviewed_worker
from tests.integration.api.test_intake_review_workflows import ROOT, command
from tests.integration.test_linked_intake_snapshot import dependencies, reader


@pytest.mark.parametrize(
    "kind,section",
    [
        ("worker", "worker_residence"),
        ("household", "party_address"),
        ("business", "party_address"),
        ("business", "worksite_address"),
    ],
)
def test_address_http_projection_keeps_sources_separate(client, monkeypatch, kind, section):
    if kind == "worker":
        target, body = reviewed_worker(client)
        outputs = command(client, f"{ROOT}/{target}/finalizations", body, 201).json()[
            "finalization"
        ]
        content = {"full_name": "Different candidate"}
    else:
        _, outputs, _ = canonical(client, kind)
        content = {"employer_type": kind, "display_name": "Different candidate"}
    draft = command(client, ROOT, {"kind": outputs["kind"], "content": content}, 201).json()[
        "current"
    ]
    target = draft["summary"]["intake_id"]
    real_get = get_intake

    def linked_row(session, intake_id) -> dict[str, Any]:
        row = real_get(session, intake_id)
        if intake_id == UUID(target):
            row["_has_link_row"] = True
        return row

    monkeypatch.setattr(routes, "get_intake", linked_row)
    monkeypatch.setattr(reader_module, "get_link_dependencies", lambda *_: dependencies(outputs))
    principal = reader(client)
    client.app.dependency_overrides[get_staff_principal] = lambda: principal
    accesses = []
    client.app.state.intake_access_sink = lambda **event: accesses.append(event)
    response = client.get(f"{ROOT}/{target}/addresses/{section}")
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["candidate"] is None
    assert result["resolved"]["line1"]
    source = (
        "residence"
        if kind == "worker"
        else "worksite"
        if section == "worksite_address"
        else "contact_details"
        if kind == "household"
        else "business_address"
    )
    assert result["source_ref"] == {key: outputs[source][key] for key in ("id", "version")}
    assert accesses == [
        {"actor_id": principal.actor_id, "intake_id": UUID(target), "section": section}
    ]
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        principal,
        permissions=principal.permissions - {f"{section}:read"},
    )
    denied = client.get(f"{ROOT}/{target}/addresses/{section}")
    assert denied.status_code == 403
    assert result["resolved"]["line1"] not in denied.text
    assert len(accesses) == 1
