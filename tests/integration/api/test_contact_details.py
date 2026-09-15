from dataclasses import replace
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from golden_rose.api.dependencies import get_staff_principal
from golden_rose.persistence.models import audit_events, command_receipts, intake_finalizations
from tests.integration.api.test_employer_finalizations import reviewed_employer
from tests.integration.api.test_intake_finalizations import client as client
from tests.integration.api.test_intake_review_workflows import ROOT, command
from tests.unit.test_employer_finalization_outputs import PARTY, content


def canonical(client, kind="household") -> tuple[Any, ...]:
    target, body = reviewed_employer(client, kind)
    refs = command(client, f"{ROOT}/{target}/finalizations", body, 201).json()["finalization"]
    principal = client.app.dependency_overrides[get_staff_principal]()
    reader = replace(
        principal, permissions=principal.permissions | {"employer_contact:details:read"}
    )
    client.app.dependency_overrides[get_staff_principal] = lambda: reader
    path = (
        f"/api/staff/v1/employers/{refs['employer']['id']}/contacts/{refs['contact']['id']}/details"
    )
    return path, refs, reader


@pytest.mark.parametrize("kind", ["household", "business"])
def test_canonical_contact_sections_without_history_writes(client, session, kind):
    path, refs, _ = canonical(client, kind)
    tables = (audit_events, command_receipts, intake_finalizations)
    before = [session.scalar(select(func.count()).select_from(t)) for t in tables]
    details = client.get(path)
    assert details.status_code == 200, details.text
    assert details.json() == {
        "contact_details_id": refs["contact_details"]["id"],
        "employer_id": refs["employer"]["id"],
        "employer_contact_id": refs["contact"]["id"],
        "version": 1,
        "phone": content(kind)["phone"],
        "representative_name": content(kind)["representative_name"],
    }
    address = client.get(path + "/address")
    assert address.status_code == (200 if kind == "household" else 404), address.text
    if kind == "household":
        assert address.json()["address"] == PARTY
    assert before == [session.scalar(select(func.count()).select_from(t)) for t in tables]
    assert client.get(path.replace(refs["employer"]["id"], str(uuid4()))).status_code == 404
    assert client.get(path.replace(refs["contact"]["id"], str(uuid4()))).status_code == 404


@pytest.mark.parametrize(
    "permission,suffix",
    [
        ("employer:read", ""),
        ("employer_contact:read", ""),
        ("employer_contact:details:read", ""),
        ("party_address:read", "/address"),
    ],
)
def test_contact_permissions_are_current(client, permission, suffix):
    path, _, reader = canonical(client)
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        reader, permissions=reader.permissions - {permission}
    )
    response = client.get(path + suffix)
    assert response.status_code == 403
    assert "Fictional" not in response.text


def test_cross_employer_contact_is_not_found(client):
    first, first_refs, _ = canonical(client)
    _, second_refs, _ = canonical(client)
    wrong = first.replace(first_refs["contact"]["id"], second_refs["contact"]["id"])
    assert client.get(wrong).status_code == 404
    assert client.get(wrong + "/address").status_code == 404
