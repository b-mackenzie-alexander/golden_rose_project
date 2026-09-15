from dataclasses import replace
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from golden_rose.api.dependencies import get_staff_principal
from golden_rose.application.intake_contracts import Schedule
from golden_rose.persistence.models import audit_events, command_receipts, intake_finalizations
from tests.integration.api.test_contact_details import canonical
from tests.integration.api.test_intake_finalizations import client as client
from tests.unit.test_employer_finalization_outputs import PARTY, WORKSITE, content


def paths(refs) -> dict[str, Any]:
    root = f"/api/staff/v1/employers/{refs['employer']['id']}"
    return {
        "business_address": f"{root}/addresses/{refs['business_address']['id']}",
        "worksite": f"{root}/worksites/{refs['worksite']['id']}",
        "worksite_address": f"{root}/worksites/{refs['worksite']['id']}/address",
        "request": f"{root}/requests/{refs['request']['id']}",
    }


@pytest.fixture
def output(client) -> tuple[Any, ...]:
    _, refs, principal = canonical(client, "business")
    reader = replace(
        principal, permissions=principal.permissions | {"worksite:read", "staffing_request:read"}
    )
    client.app.dependency_overrides[get_staff_principal] = lambda: reader
    return paths(refs), refs, reader


def test_reads_match_finalized_canonical_outputs_without_history_writes(client, session, output):
    urls, refs, _ = output
    tables = (audit_events, command_receipts, intake_finalizations)
    before = [session.scalar(select(func.count()).select_from(t)) for t in tables]
    results = {}
    for section, url in urls.items():
        response = client.get(url)
        assert response.status_code == 200, response.text
        assert response.headers["cache-control"] == "no-store"
        results[section] = response.json()
    assert results["business_address"]["address"] == PARTY
    assert results["worksite_address"]["address"] == WORKSITE
    assert results["worksite"]["worksite_id"] == refs["worksite"]["id"]
    assert "address" not in results["worksite"]
    request = results["request"]
    assert request["employer_contact_id"] == refs["contact"]["id"]
    assert request["employer_address_id"] == refs["business_address"]["id"]
    assert request["worksite_id"] == refs["worksite"]["id"]
    assert request["request_type"] == "general_labor"
    assert request["offer"] == content("business")["offer"]
    assert request["schedule"] == Schedule.model_validate(
        content("business")["schedule"]
    ).model_dump(mode="json")
    assert PARTY["line1"] not in str(request) and WORKSITE["line1"] not in str(request)
    assert before == [session.scalar(select(func.count()).select_from(t)) for t in tables]


@pytest.mark.parametrize(
    "section,permission",
    [
        ("business_address", "employer:read"),
        ("business_address", "party_address:read"),
        ("worksite", "employer:read"),
        ("worksite", "worksite:read"),
        ("worksite_address", "employer:read"),
        ("worksite_address", "worksite:read"),
        ("worksite_address", "worksite_address:read"),
        ("request", "employer:read"),
        ("request", "staffing_request:read"),
    ],
)
def test_revocation_prevents_current_reads(client, output, section, permission):
    urls, _, reader = output
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        reader, permissions=reader.permissions - {permission}
    )
    response = client.get(urls[section])
    assert response.status_code == 403
    assert "Fictional" not in response.text


@pytest.mark.parametrize("section", ["business_address", "worksite", "worksite_address", "request"])
def test_existing_wrong_parent_and_missing_share_404(client, output, section):
    urls, refs, _ = output
    _, other, principal = canonical(client, "business")
    reader = replace(
        principal, permissions=principal.permissions | {"worksite:read", "staffing_request:read"}
    )
    client.app.dependency_overrides[get_staff_principal] = lambda: reader
    wrong = client.get(urls[section].replace(refs["employer"]["id"], other["employer"]["id"]))
    missing = client.get(urls[section].replace(refs["employer"]["id"], str(uuid4())))
    assert wrong.status_code == missing.status_code == 404
    assert wrong.json() == missing.json()


def test_household_request_retains_null_business_address(client):
    _, refs, principal = canonical(client)
    reader = replace(principal, permissions=principal.permissions | {"staffing_request:read"})
    client.app.dependency_overrides[get_staff_principal] = lambda: reader
    response = client.get(
        f"/api/staff/v1/employers/{refs['employer']['id']}/requests/{refs['request']['id']}"
    )
    assert response.status_code == 200, response.text
    assert response.json()["employer_address_id"] is None
    assert response.json()["request_type"] == "household"
