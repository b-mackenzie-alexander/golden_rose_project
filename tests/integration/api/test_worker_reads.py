"""Canonical worker reads from a committed HTTP finalization, with no read-side writes."""

from dataclasses import replace
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from golden_rose.api.dependencies import get_staff_principal
from golden_rose.persistence.models import audit_events, command_receipts, intake_finalizations
from tests.integration.api.test_intake_finalizations import client as client
from tests.integration.api.test_intake_finalizations import reviewed_worker
from tests.integration.api.test_intake_review_workflows import ROOT, command


@pytest.fixture
def canonical(client):
    target, body = reviewed_worker(client)
    result = command(client, f"{ROOT}/{target}/finalizations", body, 201).json()
    principal = client.app.dependency_overrides[get_staff_principal]()
    reader = replace(
        principal, permissions=principal.permissions | {"worker:read", "worker_contact:read"}
    )
    client.app.dependency_overrides[get_staff_principal] = lambda: reader
    return client, result, reader


def test_canonical_worker_reads_match_outputs_without_history_mutations(canonical, session):
    client, result, _ = canonical
    refs = result["finalization"]
    target = refs["worker"]["id"]
    path = f"/api/staff/v1/workers/{target}"
    tables = (audit_events, command_receipts, intake_finalizations)
    before = [session.scalar(select(func.count()).select_from(table)) for table in tables]
    identity = client.get(path)
    assert identity.status_code == 200, identity.text
    assert identity.json()["contact_id"] == refs["contact"]["id"]
    assert identity.json()["residence_id"] == refs["residence"]["id"]
    assert identity.json()["preferences_id"] == refs["preferences"]["id"]
    assert "phone" not in identity.json() and "address" not in identity.json()
    for section, id_field in [
        ("contact", "worker_contact_id"),
        ("residence", "worker_residence_id"),
        ("preferences", "worker_preferences_id"),
    ]:
        response = client.get(f"{path}/{section}")
        assert response.status_code == 200, response.text
        assert response.json()[id_field] == refs[section]["id"]
        assert response.json()["version"] == refs[section]["version"]
        assert response.headers["cache-control"] == "no-store"
        if section == "contact":
            assert response.json()["phone"] == "202-555-0151"
        elif section == "residence":
            assert response.json()["address"]["line1"] == "10 Fictional Road"
        else:
            assert response.json()["self_reported"] is True
            assert response.json()["availability"] == {"mode": "flexible"}
    assert before == [session.scalar(select(func.count()).select_from(table)) for table in tables]
    assert (
        client.get(f"{ROOT}/{result['current']['summary']['intake_id']}").json()["finalization"]
        == refs
    )


@pytest.mark.parametrize(
    "section,permission",
    [
        ("", "worker:read"),
        ("/contact", "worker_contact:read"),
        ("/residence", "worker_residence:read"),
        ("/preferences", "worker:read"),
    ],
)
def test_canonical_worker_read_permission_revocation(canonical, section, permission):
    client, result, reader = canonical
    revoked = replace(reader, permissions=reader.permissions - {permission})
    client.app.dependency_overrides[get_staff_principal] = lambda: revoked
    response = client.get(
        f"/api/staff/v1/workers/{result['finalization']['worker']['id']}{section}"
    )
    assert response.status_code == 403
    assert "Fictional" not in response.text


@pytest.mark.parametrize("section", ["", "/contact", "/residence", "/preferences"])
def test_canonical_worker_scope_and_missing_are_indistinguishable(canonical, section):
    client, result, reader = canonical
    target = result["finalization"]["worker"]["id"]
    missing = client.get(f"/api/staff/v1/workers/{uuid4()}{section}")
    assert missing.status_code == 404
    scoped = replace(reader, worker_scope=frozenset())
    client.app.dependency_overrides[get_staff_principal] = lambda: scoped
    denied = client.get(f"/api/staff/v1/workers/{target}{section}")
    assert denied.status_code == 404
    assert denied.json() == missing.json()
    scoped = replace(reader, worker_scope=frozenset({UUID(target)}))
    client.app.dependency_overrides[get_staff_principal] = lambda: scoped
    assert client.get(f"/api/staff/v1/workers/{target}{section}").status_code == 200
