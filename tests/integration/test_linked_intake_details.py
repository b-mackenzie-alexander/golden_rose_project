"""Real canonical detail projection with injected references, not durable links."""

from dataclasses import replace
from typing import Any
from uuid import UUID

import pytest

from golden_rose.api.dependencies import get_staff_principal
from golden_rose.api.staff import intakes as routes
from golden_rose.application import intake_resolved_detail as resolver
from golden_rose.persistence.intakes import get_intake
from tests.integration.api.test_contact_details import canonical
from tests.integration.api.test_intake_finalizations import client as client
from tests.integration.api.test_intake_finalizations import reviewed_worker
from tests.integration.api.test_intake_review_workflows import ROOT, command
from tests.integration.test_linked_intake_snapshot import dependencies, reader


@pytest.mark.parametrize("kind", ["worker", "household", "business"])
def test_nonaddress_detail_and_stale_versions_without_address_permissions(
    client, monkeypatch, kind
):
    if kind == "worker":
        target, body = reviewed_worker(client)
        outputs = command(client, f"{ROOT}/{target}/finalizations", body, 201).json()[
            "finalization"
        ]
        candidate = {"full_name": "Different candidate"}
    else:
        _, outputs, _ = canonical(client, kind)
        candidate = {"display_name": "Different candidate", "employer_type": kind}
    draft = command(client, ROOT, {"kind": outputs["kind"], "content": candidate}, 201).json()[
        "current"
    ]
    target = draft["summary"]["intake_id"]
    refs = dependencies(outputs)
    real_get = get_intake

    def linked_row(session, intake_id) -> dict[str, Any]:
        row = real_get(session, intake_id)
        if intake_id == UUID(target):
            row["_has_link_row"] = True
        return row

    monkeypatch.setattr(routes, "get_intake", linked_row)
    monkeypatch.setattr(resolver, "get_link_dependencies", lambda *_: refs)
    principal = replace(
        reader(client),
        permissions=reader(client).permissions
        - {
            "worker_residence:read",
            "party_address:read",
            "worksite_address:read",
        },
    )
    client.app.dependency_overrides[get_staff_principal] = lambda: principal
    response = client.get(f"{ROOT}/{target}")
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["candidate"] == candidate
    assert result["resolved"]["phone"] == "202-555-0151"
    assert result["summary"]["display_name"] != "Different candidate"
    assert result["summary"]["complete"] == (kind == "worker")
    assert not {"worker_residence", "party_address", "worksite_address"} & set(
        result["summary"]["missing_fields"]
    )
    assert not result["dependency_stale"] and result["links"] == refs
    assert not any(
        field in result["resolved"] for field in ("line1", "locality", "country", "role_title")
    )
    refs[outputs["kind"]]["version"] += 1
    stale = client.get(f"{ROOT}/{target}")
    assert stale.status_code == 200, stale.text
    assert stale.json()["dependency_stale"]
    assert stale.json()["resolved"] == result["resolved"]
    denied_permission = (
        "worker_contact:read" if kind == "worker" else "employer_contact:details:read"
    )
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        principal,
        permissions=principal.permissions - {denied_permission},
    )
    denied = client.get(f"{ROOT}/{target}")
    assert denied.status_code == 403
    assert "202-555-0151" not in denied.text
