"""Real PostgreSQL HTTP acceptance for worker finalization and review gating."""

from dataclasses import replace
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from golden_rose.api.dependencies import get_settings, get_staff_directory, get_staff_principal
from golden_rose.auth.staff_directory import StaffDirectory, StaffDirectoryEntry
from golden_rose.main import create_app
from tests.integration.api.test_intake_review_workflows import ROOT, command, worker


@pytest.fixture
def client(clean_tables):
    app = create_app()
    principal = get_staff_principal(get_settings())
    finalizer = replace(principal, permissions=principal.permissions | {"intake:finalize"})
    directory = StaffDirectory(
        (
            StaffDirectoryEntry(
                finalizer.actor_id, "Fictional Finalizer", True, finalizer.permissions
            ),
        )
    )
    app.dependency_overrides[get_staff_principal] = lambda: finalizer
    app.dependency_overrides[get_staff_directory] = lambda: directory
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def reviewed_worker(client: TestClient) -> tuple[str, dict[str, Any]]:
    target = worker(client)["summary"]["intake_id"]
    reviewed = command(
        client,
        f"{ROOT}/{target}/reviews",
        {"expected_version": 1, "outcome": "intake_reviewed"},
    ).json()["current"]
    return target, {"expected_version": 2, "review_id": reviewed["latest_review"]["review_id"]}


def test_finalize_replay_and_reopen_worker_over_http(client):
    target, body = reviewed_worker(client)
    key = uuid4()
    path = f"{ROOT}/{target}/finalizations"
    first = command(client, path, body, 201, key)
    result = first.json()
    assert first.headers["idempotency-replayed"] == "false"
    assert first.headers["location"] == f"{ROOT}/{target}"
    assert result["current"]["summary"]["lifecycle"] == "finalized"
    assert result["current"]["content_version"] == 1
    assert result["result_record_version"] == 3
    assert result["finalization"]["kind"] == "worker"
    assert result["finalization"] == result["current"]["finalization"]
    assert (
        len(
            {
                result["finalization"][name]["id"]
                for name in ("worker", "contact", "residence", "preferences")
            }
        )
        == 4
    )
    assert "10 Fictional Road" not in first.text
    reopened = client.get(first.headers["location"])
    assert reopened.status_code == 200
    assert reopened.json()["finalization"] == result["finalization"]
    replay = command(client, path, body, key=key)
    assert replay.headers["idempotency-replayed"] == "true"
    assert replay.json()["finalization"] == result["finalization"]
    assert "location" not in replay.headers
    duplicate = command(client, path, body, 409)
    assert duplicate.json()["code"] == "already_finalized"


@pytest.mark.parametrize(
    "permission", ["intake:finalize", "worker_residence:read", "worker_residence:write"]
)
def test_finalization_replay_checks_current_permission_over_http(client, permission):
    target, body = reviewed_worker(client)
    key = uuid4()
    path = f"{ROOT}/{target}/finalizations"
    command(client, path, body, 201, key)
    finalizer = client.app.dependency_overrides[get_staff_principal]()
    revoked = replace(finalizer, permissions=finalizer.permissions - {permission})
    client.app.dependency_overrides[get_staff_principal] = lambda: revoked
    response = command(client, path, body, 403, key)
    assert response.json()["code"] == "forbidden"
    assert "finalization" not in response.json()


def test_worker_http_finalization_requires_current_review(client):
    target = worker(client)["summary"]["intake_id"]
    response = command(
        client,
        f"{ROOT}/{target}/finalizations",
        {"expected_version": 1, "review_id": str(uuid4())},
        409,
    )
    assert response.json()["code"] == "review_required"
    assert client.get(f"{ROOT}/{target}").json()["summary"]["lifecycle"] == "draft"


def test_employer_without_current_review_does_not_create_outputs(client):
    current = command(
        client,
        ROOT,
        {"kind": "employer", "content": {"display_name": "Fictional Finalization Employer"}},
        201,
    ).json()["current"]
    target = current["summary"]["intake_id"]
    response = command(
        client,
        f"{ROOT}/{target}/finalizations",
        {"expected_version": 1, "review_id": str(uuid4())},
        409,
    )
    assert response.json()["code"] == "review_required"
    assert client.get(f"{ROOT}/{target}").json()["summary"]["lifecycle"] == "draft"
