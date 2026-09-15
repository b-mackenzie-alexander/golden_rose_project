"""Real HTTP link, retry, and finalization acceptance on disposable PostgreSQL."""

from dataclasses import replace
from typing import Any
from uuid import UUID, uuid4

import pytest

from golden_rose.api.dependencies import get_staff_principal
from golden_rose.application import link_intake
from golden_rose.application.intake_errors import IntakeError
from tests.integration.api.test_intake_review_workflows import ROOT, command, worker
from tests.integration.test_intake_link_authority import (
    AUTHORITY_TABLES,
    EMPLOYER_TABLES,
    LINKER,
    WORKER_TABLES,
    canonical,
    dependencies,
    draft_employer,
    reference,
    review,
    rows,
)
from tests.integration.test_intake_link_authority import client as client
from tests.integration.test_intake_migrations import migration_database as migration_database


def snapshot(database) -> dict[str, Any]:
    return {
        table: rows(database, table)
        for table in (
            *AUTHORITY_TABLES,
            *WORKER_TABLES,
            *EMPLOYER_TABLES,
            "intakes",
            "intake_links",
            "intake_addresses",
            "intake_finalizations",
        )
    }


@pytest.mark.parametrize("kind", ["worker", "business", "household"])
def test_http_link_review_finalize_reuses_selected_outputs(client, migration_database, kind):
    refs = canonical(client, kind)
    target = (
        worker(client)["summary"]["intake_id"] if kind == "worker" else draft_employer(client, kind)
    )
    candidate = client.get(f"{ROOT}/{target}").json()["candidate"]
    party = "worker" if kind == "worker" else "employer"
    body = {"expected_version": 1, "party": reference(refs[party])}
    if kind != "worker":
        body.update(contact=reference(refs["contact"]), worksite=reference(refs["worksite"]))
        if kind == "business":
            body["business_address"] = reference(refs["business_address"])
    before = {
        table: rows(migration_database, table) for table in (*WORKER_TABLES, *EMPLOYER_TABLES)
    }
    response = command(client, f"{ROOT}/{target}/links", body)
    current = response.json()["current"]
    assert current["summary"]["version"] == current["content_version"] == 2
    assert current["candidate"] == candidate
    assert current["links"][party] == reference(refs[party])
    for field in ("line1", "line2", "locality", "region", "postal_code", "country"):
        assert f'"{field}"' not in response.text
    for address in ("10 Fictional Road", "10 Fictional Party Road", "20 Fictional Worksite Road"):
        assert address not in response.text
    assert {table: rows(migration_database, table) for table in before} == before
    finalized = command(client, f"{ROOT}/{target}/finalizations", review(client, target, 2), 201)
    outputs = finalized.json()["finalization"]
    for name, original in refs.items():
        if name in {"kind", "request"} or original is None:
            continue
        assert outputs[name] == {**original, "disposition": "reused"}
    for table, original in before.items():
        if kind != "worker" and table == "staffing_requests":
            assert len(rows(migration_database, table)) == len(original) + 1
        else:
            assert rows(migration_database, table) == original


def test_original_http_retry_after_replacement_and_unlink(client, migration_database):
    first, second = canonical(client), canonical(client)
    target = worker(client)["summary"]["intake_id"]
    path, key = f"{ROOT}/{target}/links", uuid4()
    original = {"expected_version": 1, "party": reference(first["worker"])}
    command(client, path, original, key=key)
    command(client, path, {"expected_version": 2, "party": reference(second["worker"])})
    command(client, path, {"expected_version": 3, "party": None})
    before = snapshot(migration_database)
    replay = command(client, path, original, key=key)
    assert replay.headers["idempotency-replayed"] == "true"
    assert replay.headers["idempotency-result-version"] == "2"
    assert replay.json()["current"]["summary"]["version"] == 4
    assert replay.json()["current"]["links"] == {}
    conflict = command(client, path, {"expected_version": 3, "party": None}, 409, key=key)
    assert conflict.json()["code"] == "idempotency_conflict"
    assert snapshot(migration_database) == before


@pytest.mark.parametrize("permission", ["intake:link", "intake:read", "worker_contact:read"])
def test_http_retry_checks_current_permissions(client, migration_database, permission):
    refs = canonical(client)
    target = worker(client)["summary"]["intake_id"]
    path, key = f"{ROOT}/{target}/links", uuid4()
    body = {"expected_version": 1, "party": reference(refs["worker"])}
    command(client, path, body, key=key)
    before = snapshot(migration_database)
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        LINKER, permissions=LINKER.permissions - {permission}
    )
    assert command(client, path, body, 403, key=key).json()["code"] == "forbidden"
    assert snapshot(migration_database) == before


def test_retry_cannot_disclose_replacement_outside_current_scope(client, migration_database):
    first, second = canonical(client), canonical(client)
    target = worker(client)["summary"]["intake_id"]
    path, key = f"{ROOT}/{target}/links", uuid4()
    body = {"expected_version": 1, "party": reference(first["worker"])}
    command(client, path, body, key=key)
    command(client, path, {"expected_version": 2, "party": reference(second["worker"])})
    before = snapshot(migration_database)
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        LINKER, worker_scope=frozenset({UUID(first["worker"]["id"])})
    )
    assert command(client, path, body, 404, key=key).json()["code"] == "not_found"
    assert snapshot(migration_database) == before


def test_projection_failure_rolls_back_and_original_key_recovers(
    client, migration_database, monkeypatch
):
    refs = canonical(client)
    target = worker(client)["summary"]["intake_id"]
    path, key = f"{ROOT}/{target}/links", uuid4()
    body = {"expected_version": 1, "party": reference(refs["worker"])}
    before = snapshot(migration_database)

    def unavailable(*args, **kwargs) -> None:
        raise IntakeError("persistence_unavailable", 503)

    with monkeypatch.context() as patch:
        patch.setattr(link_intake, "intake_detail", unavailable)
        response = command(client, path, body, 503, key=key)
        assert response.headers["retry-after"] == "1"
    assert snapshot(migration_database) == before
    assert command(client, path, body, key=key).headers["idempotency-replayed"] == "false"
    assert dependencies(migration_database, target)["worker"] == reference(refs["worker"])


@pytest.mark.parametrize(
    "case,code",
    [
        ("stale", "version_conflict"),
        ("unchanged", "no_change"),
        ("wrong_parent", "not_found"),
    ],
)
def test_invalid_http_link_preserves_all_rows(client, migration_database, case, code):
    first, second = canonical(client, "business"), canonical(client, "business")
    target = draft_employer(client, "business")
    path = f"{ROOT}/{target}/links"
    body = {"expected_version": 1, "party": reference(first["employer"])}
    command(client, path, body)
    if case != "stale":
        body["expected_version"] = 2
    if case == "wrong_parent":
        body["contact"] = reference(second["contact"])
    before = snapshot(migration_database)
    assert (
        command(client, path, body, 404 if case == "wrong_parent" else 409).json()["code"] == code
    )
    assert snapshot(migration_database) == before
