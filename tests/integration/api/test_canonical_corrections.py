"""Every correction route exercises real PostgreSQL, strict replies and field rights."""

from dataclasses import replace
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from golden_rose.api.dependencies import get_db_session, get_staff_principal
from tests.integration.api.test_employer_finalizations import reviewed_employer
from tests.integration.api.test_intake_finalizations import client as client
from tests.integration.api.test_intake_finalizations import reviewed_worker
from tests.integration.api.test_intake_review_workflows import ROOT, command
from tests.integration.test_canonical_corrections import CORRECTOR
from tests.unit.test_canonical_correction_contracts import CASES

ROUTES = [
    ("worker", "worker", "/workers/{worker}/corrections", 0),
    ("worker", "worker_contact", "/workers/{worker}/contact/corrections", 1),
    ("worker", "worker_residence", "/workers/{worker}/residence/corrections", 2),
    ("worker", "worker_preferences", "/workers/{worker}/preferences/corrections", 3),
    (
        "household",
        "employer_contact_details",
        "/employers/{employer}/contacts/{contact}/details/corrections",
        4,
    ),
    (
        "household",
        "employer_contact_details",
        "/employers/{employer}/contacts/{contact}/details/address/corrections",
        5,
    ),
    (
        "business",
        "employer_address",
        "/employers/{employer}/addresses/{business_address}/corrections",
        6,
    ),
    ("business", "worksite", "/employers/{employer}/worksites/{worksite}/address/corrections", 7),
    ("household", "staffing_request", "/employers/{employer}/requests/{request}/corrections", 8),
]


@pytest.mark.parametrize("kind,entity,path,index", ROUTES)
def test_each_supported_section_corrects_current_facts_with_atomic_reason_audit(
    client, session, kind, entity, path, index
):
    intake_id, body = (
        reviewed_worker(client) if kind == "worker" else reviewed_employer(client, kind)
    )
    result = command(client, f"{ROOT}/{intake_id}/finalizations", body, 201).json()
    refs = result["finalization"]

    def runtime_session():
        with Session(session.get_bind()) as runtime:
            runtime.execute(text("SET LOCAL ROLE golden_rose_runtime"))
            yield runtime

    client.app.dependency_overrides[get_db_session] = runtime_session
    client.app.dependency_overrides[get_staff_principal] = lambda: CORRECTOR
    route = "/api/staff/v1" + path.format(
        **{k: v["id"] for k, v in refs.items() if k != "kind" and v}
    )
    payload = {
        "expected_version": 1,
        "reason_text": "Fictional correction reason",
        **CASES[index][1],
    }
    key = uuid4()
    response = command(client, route, payload, key=key)
    value = response.json()
    assert set(value) == {"command_id", "event_id", "result_record_version", "target"}
    assert value["result_record_version"] == 2 and value["target"]["entity_type"] == entity
    assert command(client, route, payload, key=key).json() == value
    assert (
        command(client, route, {**payload, "reason_text": "Fictional changed"}, 409, key).json()[
            "code"
        ]
        == "idempotency_conflict"
    )
    assert session.scalar(text("SELECT count(*) FROM canonical_corrections")) == 1
    assert client.get(f"{ROOT}/{intake_id}").json()["finalization"] == refs
    history_path = f"/api/staff/v1/canonical-corrections/{value['event_id']}"
    assert client.get(history_path).status_code == 403
    reader = replace(
        CORRECTOR, permissions=CORRECTOR.permissions | {"intake:restricted_history:read"}
    )
    client.app.dependency_overrides[get_staff_principal] = lambda: reader
    history = client.get(history_path)
    assert history.status_code == 200, history.text
    assert history.json()["after"] == CASES[index][1]
    assert history.json()["reason_text"] == payload["reason_text"]
    assert "no-store" in history.headers["cache-control"]
    assert session.scalar(text("SELECT count(*) FROM canonical_corrections")) == 1


@pytest.mark.parametrize(
    "case,field,invalid",
    [
        (3, "availability", {"mode": "weekly"}),
        (8, "schedule", {"mode": "specified"}),
        (5, "address", {}),
    ],
)
def test_database_rejects_incomplete_sections_even_with_full_correction_evidence(
    client, session, monkeypatch, case, field, invalid
):
    """Bypass only DTO validation; retain the actual complete atomic authority writer."""
    from golden_rose.persistence.canonical_corrections import SPECS

    kind, _, path, index = ROUTES[case]
    intake_id, body = (
        reviewed_worker(client) if kind == "worker" else reviewed_employer(client, kind)
    )
    refs = command(client, f"{ROOT}/{intake_id}/finalizations", body, 201).json()["finalization"]
    client.app.dependency_overrides[get_staff_principal] = lambda: CORRECTOR
    route = "/api/staff/v1" + path.format(
        **{k: v["id"] for k, v in refs.items() if k != "kind" and v}
    )
    model = next(spec.model for spec in SPECS.values() if spec.model.__name__ == CASES[index][0])
    values = {**CASES[index][1], field: invalid}
    monkeypatch.setattr(model, "section_values", lambda self: values)
    before = session.scalar(text("SELECT count(*) FROM command_receipts"))
    command(
        client,
        route,
        {"expected_version": 1, "reason_text": "Fictional structural probe", **CASES[index][1]},
        503,
    )
    assert session.scalar(text("SELECT count(*) FROM canonical_corrections")) == 0
    assert session.scalar(text("SELECT count(*) FROM command_receipts")) == before


def test_contact_sections_share_one_version_and_retry_survives_parent_type_change(client, session):
    from uuid import UUID

    from golden_rose.application.revise_draft_employer import revise_draft_employer
    from tests.integration.test_intake_commands import Clock

    intake_id, body = reviewed_employer(client, "household")
    refs = command(client, f"{ROOT}/{intake_id}/finalizations", body, 201).json()["finalization"]
    principal = replace(CORRECTOR, permissions=CORRECTOR.permissions | {"employer:draft:revise"})
    client.app.dependency_overrides[get_staff_principal] = lambda: principal
    base = (
        f"/api/staff/v1/employers/{refs['employer']['id']}/contacts/{refs['contact']['id']}/details"
    )
    address = {"expected_version": 1, "reason_text": "Fictional address correction", **CASES[5][1]}
    key = uuid4()
    first = command(client, base + "/address/corrections", address, key=key).json()
    details = {
        "expected_version": 1,
        "reason_text": "Fictional representative correction",
        **CASES[4][1],
    }
    assert command(client, base + "/corrections", details, 409).json()["code"] == "version_conflict"
    command(client, base + "/corrections", {**details, "expected_version": 2})
    revise_draft_employer(
        session=session,
        principal=principal,
        command_id=uuid4(),
        employer_id=UUID(refs["employer"]["id"]),
        expected_version=1,
        employer_type="business",
        display_name="Fictional Reclassified",
        clock=Clock(),
    )
    replay = command(client, base + "/address/corrections", address, key=key).json()
    assert replay["event_id"] == first["event_id"]
    assert replay["target"]["current_version"] == 3
    command(client, base + "/address/corrections", {**address, "expected_version": 3}, 422)


@pytest.mark.parametrize("field", ["start_local", "end_local"])
def test_null_weekly_times_cannot_pass_database_completeness(connection, field):
    import json

    value: dict[str, Any] = {
        "mode": "weekly",
        "time_zone": "UTC",
        "ranges": [
            {"weekday": 1, "start_local": "09:00", "end_local": "10:00", "end_day_offset": 0}
        ],
    }
    value["ranges"][0][field] = None
    assert (
        connection.scalar(
            text("SELECT canonical_details_complete('availability',CAST(:value AS jsonb))"),
            {"value": json.dumps(value)},
        )
        is False
    )
