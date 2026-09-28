"""Real PostgreSQL acceptance for PR B's review and follow-up authority."""

from dataclasses import replace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import func, select

from golden_rose.api.dependencies import (
    get_settings,
    get_staff_directory,
    get_staff_principal,
    resolve_staff_principal_for_settings,
)
from golden_rose.auth.staff_directory import StaffDirectory, StaffDirectoryEntry
from golden_rose.main import create_app
from golden_rose.persistence.models import audit_events

ROOT = "/api/staff/v1/intakes"
CATALOG = "/api/staff/v1/work-interests"
SECOND = UUID("33333333-3333-4333-8333-333333333333")


@pytest.fixture
def client(clean_tables):
    app = create_app()
    principal = resolve_staff_principal_for_settings(get_settings())
    directory = StaffDirectory(
        (
            StaffDirectoryEntry(
                principal.actor_id, "Fictional Reviewer", True, principal.permissions
            ),
            StaffDirectoryEntry(
                SECOND,
                "Fictional Follow-up Staff",
                True,
                frozenset({"intake:read", "intake:follow_up"}),
            ),
        )
    )
    app.dependency_overrides[get_staff_directory] = lambda: directory
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def command(
    client: TestClient, path: str, body: dict[str, Any], status: int = 200, key: UUID | None = None
) -> Response:
    response = client.post(path, json=body, headers={"Idempotency-Key": str(key or uuid4())})
    assert response.status_code == status, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    if status < 400:
        assert response.headers["idempotency-result-version"] == str(
            response.json()["result_record_version"]
        )
    return cast(Response, response)


def worker(
    client: TestClient, *, complete: bool = True, interests: dict[str, Any] | None = None
) -> dict[str, Any]:
    content: dict[str, Any] = {"full_name": "Fictional Review Worker"}
    if complete:
        content.update(
            phone="202-555-0151",
            interests=interests or {"other_description": "Fictional gardening"},
            availability={"mode": "flexible"},
            residential_address={
                "line1": "10 Fictional Road",
                "locality": "Fictional City",
                "country": "US",
                "region": "NY",
                "postal_code": "10001",
            },
        )
    return cast(
        dict[str, Any],
        command(client, ROOT, {"kind": "worker", "content": content}, 201).json()["current"],
    )


def followup_body(version: int, owner: UUID | None = None) -> dict[str, Any]:
    return {
        "expected_version": version,
        "outcome": "needs_follow_up",
        "reason_code": "clarification",
        "reason_text": "Fictional protected reason",
        "note": "Fictional protected note",
        "owner_staff_id": str(owner or get_settings().synthetic_staff_id),
        "next_follow_up_at": "2020-01-01T12:00:00Z",
        "time_zone": "UTC",
    }


def test_review_binds_actor_time_and_exact_version(client):
    current = worker(client)
    target = current["summary"]["intake_id"]
    body = {
        "expected_version": 1,
        "outcome": "intake_reviewed",
        "note": "Fictional private review note",
    }
    key = uuid4()
    response = command(client, f"{ROOT}/{target}/reviews", body, key=key)
    result = response.json()["current"]
    assert result["summary"]["version"] == 2 and result["content_version"] == 1
    assert result["summary"]["review_status"] == "current"
    assert result["latest_review"]["actor_display_name"] == "Fictional Reviewer"
    assert result["latest_review"]["reviewed_record_version"] == 1
    assert "Fictional private review note" not in response.text
    replay = command(client, f"{ROOT}/{target}/reviews", body, key=key)
    assert replay.headers["idempotency-replayed"] == "true"
    assert replay.json()["result_record_version"] == 2
    history = client.post(f"{ROOT}/{target}/history/query", json={}).json()
    assert [item["content_version"] for item in history["items"]] == [1, 1]
    assert "Fictional private review note" not in str(history)
    event = history["items"][0]["event_id"]
    protected = client.get(f"{ROOT}/{target}/history/{event}/restricted")
    assert protected.status_code == 200, protected.text
    assert protected.json()["note"] == body["note"]
    assert (
        protected.json()["reviewed_content"]["addresses"]["worker_residence"]["line1"]
        == "10 Fictional Road"
    )


def test_follow_up_version_does_not_stale_content_review(client):
    current = worker(client)
    target = current["summary"]["intake_id"]
    command(client, f"{ROOT}/{target}/reviews", followup_body(1))
    result = command(
        client, f"{ROOT}/{target}/reviews", {"expected_version": 2, "outcome": "intake_reviewed"}
    ).json()["current"]
    assert result["summary"]["review_status"] == "current"
    assert result["summary"]["follow_up"]["overdue"] is True
    attempt = {
        "expected_version": 3,
        "action": "attempt",
        "reason_text": "Fictional contact attempt",
        "note": "Fictional attempt note",
        "owner_staff_id": str(get_settings().synthetic_staff_id),
        "next_follow_up_at": "2020-01-02T12:00:00Z",
        "time_zone": "UTC",
        "method": "phone",
        "outcome": "information_received",
    }
    result = command(client, f"{ROOT}/{target}/follow-ups", attempt).json()["current"]
    assert result["summary"]["version"] == 4 and result["content_version"] == 1
    assert result["summary"]["review_status"] == "current"
    events = client.post(f"{ROOT}/{target}/history/query", json={}).json()["items"]
    protected = client.get(f"{ROOT}/{target}/history/{events[0]['event_id']}/restricted")
    assert protected.status_code == 200, protected.text
    assert protected.json()["follow_up"]["method"] == "phone"
    assert protected.json()["follow_up"]["reason_text"] == "Fictional contact attempt"
    assert protected.json()["note"] == "Fictional attempt note"
    result = command(client, f"{ROOT}/{target}/reviews", followup_body(4)).json()["current"]
    assert result["summary"]["review_status"] == "needs_follow_up"
    assert result["content_version"] == 1


def test_relevant_edit_requires_new_review_without_erasing_prior_review(client):
    current = worker(client)
    target = current["summary"]["intake_id"]
    reviewed = command(
        client, f"{ROOT}/{target}/reviews", {"expected_version": 1, "outcome": "intake_reviewed"}
    ).json()["current"]
    candidate = dict(current["candidate"], full_name="Fictional Changed Worker")
    result = command(
        client, f"{ROOT}/{target}/revisions", {"expected_version": 2, "content": candidate}
    ).json()["current"]
    assert result["summary"]["review_status"] == "stale"
    assert result["latest_review"]["review_id"] == reviewed["latest_review"]["review_id"]
    assert result["content_version"] == 2


def test_incomplete_review_and_existing_follow_up_required(client):
    target = worker(client, complete=False)["summary"]["intake_id"]
    response = command(
        client,
        f"{ROOT}/{target}/reviews",
        {"expected_version": 1, "outcome": "intake_reviewed"},
        422,
    )
    assert set(response.json()["missing_fields"]) == {
        "phone",
        "interests",
        "availability",
        "worker_residence",
    }
    command(
        client,
        f"{ROOT}/{target}/follow-ups",
        {
            "expected_version": 1,
            "action": "reschedule",
            "reason_text": "Fictional reason",
            "owner_staff_id": str(SECOND),
            "next_follow_up_at": "2020-01-01T12:00:00Z",
            "time_zone": "UTC",
        },
        422,
    )
    assert client.get(f"{ROOT}/{target}").json()["summary"]["version"] == 1


def test_reassignment_preserves_prior_owner_and_deadline(client):
    target = worker(client, complete=False)["summary"]["intake_id"]
    command(client, f"{ROOT}/{target}/reviews", followup_body(1))
    body = {
        "expected_version": 2,
        "action": "reassign",
        "reason_text": "Fictional reassignment",
        "owner_staff_id": str(SECOND),
        "next_follow_up_at": "2020-01-03T12:00:00Z",
        "time_zone": "UTC",
    }
    result = command(client, f"{ROOT}/{target}/follow-ups", body).json()["current"]
    assert result["summary"]["follow_up"]["owner_staff_id"] == str(SECOND)
    history = client.post(f"{ROOT}/{target}/history/query", json={}).json()["items"]
    assert history[0]["owner_staff_id"] == str(SECOND)
    assert history[1]["owner_staff_id"] == str(get_settings().synthetic_staff_id)
    assert history[0]["next_follow_up_at"] != history[1]["next_follow_up_at"]


@pytest.mark.parametrize("missing", ["intake:review", "worker_residence:read"])
def test_ordinary_staff_cannot_review_without_delegation(client, missing):
    target = worker(client)["summary"]["intake_id"]
    principal = resolve_staff_principal_for_settings(get_settings())
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        principal, permissions=principal.permissions - {missing}
    )
    command(
        client,
        f"{ROOT}/{target}/reviews",
        {"expected_version": 1, "outcome": "intake_reviewed"},
        403,
    )


def test_review_requires_read_not_write_and_revoked_retry_fails(client):
    target = worker(client)["summary"]["intake_id"]
    principal = resolve_staff_principal_for_settings(get_settings())
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        principal, permissions=principal.permissions - {"worker_residence:write"}
    )
    body = {"expected_version": 1, "outcome": "intake_reviewed"}
    key = uuid4()
    command(client, f"{ROOT}/{target}/reviews", body, key=key)
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        principal, permissions=principal.permissions - {"intake:review"}
    )
    command(client, f"{ROOT}/{target}/reviews", body, 403, key=key)


def test_retired_interest_requires_current_selection(client):
    catalog = command(
        client,
        CATALOG,
        {
            "code": "fictional_gardening",
            "label_en": "Fictional Gardening",
            "label_es": "Jardinería ficticia",
        },
        201,
    ).json()["current"]
    target = worker(
        client,
        interests={"selections": [{"interest_id": catalog["interest_id"], "catalog_version": 1}]},
    )["summary"]["intake_id"]
    command(
        client, f"{ROOT}/{target}/reviews", {"expected_version": 1, "outcome": "intake_reviewed"}
    )
    command(
        client,
        f"{CATALOG}/{catalog['interest_id']}/revisions",
        {
            "expected_version": 1,
            "label_en": catalog["label_en"],
            "label_es": catalog["label_es"],
            "active": False,
        },
    )
    assert client.get(f"{ROOT}/{target}").json()["summary"]["review_status"] == "stale"
    command(
        client,
        f"{ROOT}/{target}/reviews",
        {"expected_version": 2, "outcome": "intake_reviewed"},
        422,
    )


def test_review_payload_change_same_key_and_stale_version_do_not_write(client, session):
    target = worker(client)["summary"]["intake_id"]
    key = uuid4()
    body = {"expected_version": 1, "outcome": "intake_reviewed"}
    command(client, f"{ROOT}/{target}/reviews", body, key=key)
    command(client, f"{ROOT}/{target}/reviews", dict(body, note="Changed"), 409, key=key)
    command(client, f"{ROOT}/{target}/reviews", body, 409)
    assert session.scalar(select(func.count()).select_from(audit_events)) == 2


def test_incomplete_review_preserves_explicit_absent_address_snapshot(client):
    current = worker(client, complete=False)
    target = current["summary"]["intake_id"]
    command(client, f"{ROOT}/{target}/reviews", followup_body(1))
    history = client.post(f"{ROOT}/{target}/history/query", json={}).json()
    event = history["items"][0]["event_id"]
    response = client.get(f"{ROOT}/{target}/history/{event}/restricted")
    assert response.status_code == 200, response.text
    assert response.json()["reviewed_content"]["addresses"] == {"worker_residence": None}


def test_history_keyset_scope_and_protected_access(client):
    target = worker(client)["summary"]["intake_id"]
    command(
        client, f"{ROOT}/{target}/reviews", {"expected_version": 1, "outcome": "intake_reviewed"}
    )
    command(client, f"{ROOT}/{target}/reviews", followup_body(2))
    query = f"{ROOT}/{target}/history/query"
    first = client.post(query, json={"page_size": 1}).json()
    second = client.post(query, json={"page_size": 1, "cursor": first["next_cursor"]}).json()
    third = client.post(query, json={"page_size": 1, "cursor": second["next_cursor"]}).json()
    assert [p["items"][0]["version"] for p in [first, second, third]] == [3, 2, 1]
    assert [p["items"][0]["content_version"] for p in [first, second, third]] == [1, 1, 1]
    assert third["next_cursor"] is None
    for body in [{"page_size": 2, "cursor": first["next_cursor"]}, {"cursor": "tampered"}]:
        assert client.post(query, json=body).status_code == 422
    principal = resolve_staff_principal_for_settings(get_settings())
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        principal, actor_id=SECOND
    )
    assert (
        client.post(query, json={"page_size": 1, "cursor": first["next_cursor"]}).status_code == 422
    )
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        principal, intake_scope=frozenset()
    )
    assert client.post(query, json={"cursor": "tampered"}).status_code == 404
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        principal, permissions=principal.permissions - {"intake:restricted_history:read"}
    )
    event = first["items"][0]["event_id"]
    assert client.get(f"{ROOT}/{target}/history/{event}/restricted").status_code == 403
    client.app.dependency_overrides[get_staff_principal] = lambda: principal
    assert client.get(f"{ROOT}/{target}/history/{uuid4()}/restricted").status_code == 404
    assert (
        client.get(
            f"{ROOT}/{target}/history/{third['items'][0]['event_id']}/restricted"
        ).status_code
        == 404
    )


def test_owner_options_bind_directory_and_reject_ineligible_assignment(client):
    target = worker(client, complete=False)["summary"]["intake_id"]
    query = f"{ROOT}/{target}/follow-up-owners/query"
    first = client.post(query, json={"page_size": 1}).json()
    second = client.post(query, json={"page_size": 1, "cursor": first["next_cursor"]}).json()
    assert second["items"] == [
        {"staff_id": str(SECOND), "display_name": "Fictional Follow-up Staff"}
    ]
    assert second["next_cursor"] is None
    principal = resolve_staff_principal_for_settings(get_settings())
    for entry in [
        StaffDirectoryEntry(SECOND, "Inactive Fictional", False, principal.permissions),
        StaffDirectoryEntry(
            SECOND, "Outside Scope Fictional", True, principal.permissions, frozenset()
        ),
        StaffDirectoryEntry(SECOND, "No Permission Fictional", True, frozenset({"intake:read"})),
    ]:
        client.app.dependency_overrides[get_staff_directory] = lambda entry=entry: StaffDirectory(
            (
                StaffDirectoryEntry(
                    principal.actor_id, "Fictional Reviewer", True, principal.permissions
                ),
                entry,
            )
        )
        assert (
            client.post(query, json={"page_size": 1, "cursor": first["next_cursor"]}).status_code
            == 422
        )
        command(client, f"{ROOT}/{target}/reviews", followup_body(1, SECOND), 422)
    command(client, f"{ROOT}/{target}/reviews", followup_body(1, uuid4()), 422)
    assert client.get(f"{ROOT}/{target}").json()["summary"]["version"] == 1


def test_catalog_paging_replay_history_and_reselection(client, session):
    key = uuid4()
    body = {
        "code": "_fictional",
        "label_en": "Fictional Gardening",
        "label_es": "Jardinería ficticia",
    }
    initial = command(client, CATALOG, body, 201, key).json()
    target = initial["current"]["interest_id"]
    command(client, CATALOG, body, 200, key)
    command(client, CATALOG, {**body, "label_en": "Changed"}, 409, key)
    command(client, CATALOG, body, 409)
    second = command(client, CATALOG, {**body, "code": "2_fictional"}, 201).json()["current"]
    first_page = client.post(f"{CATALOG}/query", json={"page_size": 1}).json()
    last_page = client.post(
        f"{CATALOG}/query", json={"page_size": 1, "cursor": first_page["next_cursor"]}
    ).json()
    assert {first_page["items"][0]["interest_id"], last_page["items"][0]["interest_id"]} == {
        target,
        second["interest_id"],
    }
    assert last_page["next_cursor"] is None
    assert (
        client.post(
            f"{CATALOG}/query",
            json={"page_size": 1, "cursor": first_page["next_cursor"], "include_retired": True},
        ).status_code
        == 422
    )
    assert client.post(f"{CATALOG}/query", json={"cursor": "invalid"}).status_code == 422
    revision = {
        "expected_version": 1,
        "label_en": body["label_en"],
        "label_es": body["label_es"],
        "active": True,
    }
    command(client, f"{CATALOG}/{target}/revisions", revision, 409)
    command(client, f"{CATALOG}/{uuid4()}/revisions", revision, 404)
    revision_key = uuid4()
    command(
        client, f"{CATALOG}/{target}/revisions", {**revision, "active": False}, key=revision_key
    )
    command(
        client, f"{CATALOG}/{target}/revisions", {**revision, "active": False}, key=revision_key
    )
    command(client, f"{CATALOG}/{target}/revisions", revision, 409)
    replay = command(client, CATALOG, body, key=key).json()
    assert replay["result_record_version"] == 1 and replay["current"]["version"] == 2
    active = client.post(f"{CATALOG}/query", json={}).json()["items"]
    assert [item["interest_id"] for item in active] == [second["interest_id"]]
    assert len(client.post(f"{CATALOG}/query", json={"include_retired": True}).json()["items"]) == 2
    from golden_rose.persistence.models import work_interest_versions

    assert (
        session.execute(select(func.count()).select_from(work_interest_versions)).scalar_one() == 3
    )
    principal = resolve_staff_principal_for_settings(get_settings())
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        principal, permissions=principal.permissions - {"work_interest:manage"}
    )
    command(client, CATALOG, body, 403, key)
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        principal, permissions=principal.permissions - {"work_interest:read"}
    )
    assert client.post(f"{CATALOG}/query", json={"cursor": "bad"}).status_code == 403


def test_catalog_selection_validation_and_read_permissions(client):
    invalid = {"selections": [{"interest_id": str(uuid4()), "catalog_version": 1}]}
    command(client, ROOT, {"kind": "worker", "content": {"interests": invalid}}, 422)
    item = command(
        client, CATALOG, {"code": "fictional", "label_en": "Fictional", "label_es": "Ficticio"}, 201
    ).json()["current"]
    selected = {"selections": [{"interest_id": item["interest_id"], "catalog_version": 1}]}
    target = worker(client, interests=selected)["summary"]["intake_id"]
    command(
        client, f"{ROOT}/{target}/reviews", {"expected_version": 1, "outcome": "intake_reviewed"}
    )
    event = client.post(f"{ROOT}/{target}/history/query", json={}).json()["items"][0]["event_id"]
    principal = resolve_staff_principal_for_settings(get_settings())
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        principal, permissions=principal.permissions - {"work_interest:read"}
    )
    command(
        client,
        f"{ROOT}/{target}/reviews",
        {"expected_version": 2, "outcome": "intake_reviewed"},
        403,
    )
    assert client.get(f"{ROOT}/{target}/history/{event}/restricted").status_code == 403
    command(client, ROOT, {"kind": "worker", "content": {"interests": selected}}, 403)


@pytest.mark.parametrize("same_key", [True, False])
def test_concurrent_reviews_have_one_result_and_atomic_audit(client, session, same_key):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from golden_rose.persistence.models import command_receipts, intake_reviews

    target = worker(client)["summary"]["intake_id"]
    barrier = Barrier(2)
    keys = [uuid4(), uuid4()]
    if same_key:
        keys[1] = keys[0]

    def send(key):
        barrier.wait(timeout=10)
        return client.post(
            f"{ROOT}/{target}/reviews",
            json={"expected_version": 1, "outcome": "intake_reviewed"},
            headers={"Idempotency-Key": str(key)},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(send, keys))
    assert sorted(response.status_code for response in responses) == (
        [200, 200] if same_key else [200, 409]
    )
    if same_key:
        assert sorted(response.headers["idempotency-replayed"] for response in responses) == [
            "false",
            "true",
        ]
    assert session.execute(select(func.count()).select_from(intake_reviews)).scalar_one() == 1
    assert session.execute(select(func.count()).select_from(command_receipts)).scalar_one() == 2
    assert session.execute(select(func.count()).select_from(audit_events)).scalar_one() == 2


@pytest.mark.parametrize("operation", ["review", "catalog"])
def test_workflow_failure_rolls_back_receipt_event_and_domain(
    client, session, monkeypatch, operation
):
    from sqlalchemy.exc import SQLAlchemyError

    from golden_rose.application import review_intake, work_interests
    from golden_rose.persistence.models import (
        command_receipts,
        intake_reviews,
        work_interest_versions,
    )
    from golden_rose.persistence.models import work_interests as catalog_table

    target = worker(client)["summary"]["intake_id"]
    module = review_intake if operation == "review" else work_interests
    original = module.write_authority

    def fail_after_authority(**kwargs):
        original(**kwargs)
        raise SQLAlchemyError("Fictional injected failure")

    monkeypatch.setattr(module, "write_authority", fail_after_authority)
    key = uuid4()
    if operation == "review":
        path, body = (
            f"{ROOT}/{target}/reviews",
            {"expected_version": 1, "outcome": "intake_reviewed"},
        )
    else:
        path, body = CATALOG, {"code": "fictional", "label_en": "Fictional", "label_es": "Ficticio"}
    command(client, path, body, 503, key)
    assert client.get(f"{ROOT}/{target}").json()["summary"]["version"] == 1
    assert session.execute(select(func.count()).select_from(command_receipts)).scalar_one() == 1
    assert session.execute(select(func.count()).select_from(audit_events)).scalar_one() == 1
    for table in [intake_reviews, catalog_table, work_interest_versions]:
        assert session.execute(select(func.count()).select_from(table)).scalar_one() == 0
    session.rollback()
    monkeypatch.setattr(module, "write_authority", original)
    command(client, path, body, 200 if operation == "review" else 201, key)


def test_other_interest_does_not_hide_retired_selection_in_completeness(client):
    item = command(
        client, CATALOG, {"code": "fictional", "label_en": "Fictional", "label_es": "Ficticio"}, 201
    ).json()["current"]
    target = worker(
        client,
        interests={
            "other_description": "Fictional other",
            "selections": [{"interest_id": item["interest_id"], "catalog_version": 1}],
        },
    )["summary"]["intake_id"]
    command(
        client,
        f"{CATALOG}/{item['interest_id']}/revisions",
        {
            "expected_version": 1,
            "label_en": item["label_en"],
            "label_es": item["label_es"],
            "active": False,
        },
    )
    summary = client.get(f"{ROOT}/{target}").json()["summary"]
    assert summary["complete"] is False
    assert "interests" in summary["missing_fields"]


@pytest.mark.parametrize("replay", [False, True])
def test_review_rechecks_catalog_rights_after_initial_snapshot(client, monkeypatch, replay):
    from golden_rose.application import review_intake

    item = command(
        client, CATALOG, {"code": "fictional", "label_en": "Fictional", "label_es": "Ficticio"}, 201
    ).json()["current"]
    target = worker(
        client,
        interests={"selections": [{"interest_id": item["interest_id"], "catalog_version": 1}]},
    )["summary"]["intake_id"]
    key = uuid4()
    body = {"expected_version": 1, "outcome": "intake_reviewed"}
    if replay:
        command(client, f"{ROOT}/{target}/reviews", body, key=key)
    principal = resolve_staff_principal_for_settings(get_settings())
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        principal, permissions=principal.permissions - {"work_interest:read"}
    )
    from golden_rose.persistence.intakes import get_intake

    original = get_intake
    calls = 0

    def stale_initial_snapshot(*args, **kwargs):
        nonlocal calls
        row = original(*args, **kwargs)
        calls += 1
        if calls == 1:
            # Simulate a selection added after the first unlocked read; the locked
            # command/current replay read still observes the actual persisted row.
            return {
                **row,
                "content": {
                    **row["content"],
                    "interests": {"other_description": "Fictional other"},
                },
            }
        return row

    monkeypatch.setattr(review_intake, "get_intake", stale_initial_snapshot)
    command(client, f"{ROOT}/{target}/reviews", body, 403, key)
    assert client.get(f"{ROOT}/{target}").json()["summary"]["version"] == (2 if replay else 1)


@pytest.mark.parametrize("kind", ["household", "business"])
def test_employer_review_protects_both_address_sections(client, kind):
    address = {"line1": "7 Fictional Street", "locality": "Fictional City", "country": "CA"}
    content = {
        "employer_type": kind,
        "display_name": "Fictional Employer",
        "representative_name": "Fictional Representative",
        "phone": "202-555-0111",
        "role_title": "Fictional gardener",
        "duties_summary": "Fictional gardening",
        "worker_count": 2,
        "schedule": {"mode": "to_be_discussed"},
        "offer": {"minimum": "20", "currency": "CAD", "basis": "hour", "per_worker": True},
        "party_address": address,
        "worksite_address": address,
    }
    current = command(client, ROOT, {"kind": "employer", "content": content}, 201).json()["current"]
    target = current["summary"]["intake_id"]
    assert current["summary"]["complete"] is True
    body = {"expected_version": 1, "outcome": "intake_reviewed"}
    principal = resolve_staff_principal_for_settings(get_settings())
    for permission in ["party_address:read", "worksite_address:read"]:
        client.app.dependency_overrides[get_staff_principal] = lambda permission=permission: (
            replace(principal, permissions=principal.permissions - {permission})
        )
        command(client, f"{ROOT}/{target}/reviews", body, 403)
    client.app.dependency_overrides[get_staff_principal] = lambda: replace(
        principal,
        permissions=principal.permissions - {"party_address:write", "worksite_address:write"},
    )
    reviewed = command(client, f"{ROOT}/{target}/reviews", body).json()["current"]
    assert reviewed["summary"]["review_status"] == "current"
    history = client.post(f"{ROOT}/{target}/history/query", json={}).json()
    event = history["items"][0]["event_id"]
    assert "Fictional Street" not in str(history)
    calls = []
    client.app.state.intake_access_sink = lambda **kwargs: calls.append(kwargs)
    protected = client.get(f"{ROOT}/{target}/history/{event}/restricted")
    assert protected.status_code == 200, protected.text
    assert protected.json()["reviewed_content"]["addresses"] == {
        "party_address": address,
        "worksite_address": address,
    }
    assert set(calls[0]) == {"actor_id", "intake_id", "section"}
    for permission in [
        "party_address:read",
        "worksite_address:read",
        "intake:restricted_history:read",
    ]:
        client.app.dependency_overrides[get_staff_principal] = lambda permission=permission: (
            replace(principal, permissions=principal.permissions - {permission})
        )
        assert client.get(f"{ROOT}/{target}/history/{event}/restricted").status_code == 403
    assert len(calls) == 1


def test_followup_reschedule_enforces_existing_owner_and_reassignment_change(client):
    target = worker(client, complete=False)["summary"]["intake_id"]
    command(client, f"{ROOT}/{target}/reviews", followup_body(1))
    body = {
        "expected_version": 2,
        "action": "reschedule",
        "reason_text": "Fictional revised date",
        "owner_staff_id": str(get_settings().synthetic_staff_id),
        "next_follow_up_at": "2030-01-01T12:00:00Z",
        "time_zone": "UTC",
    }
    command(client, f"{ROOT}/{target}/follow-ups", {**body, "owner_staff_id": str(SECOND)}, 422)
    command(client, f"{ROOT}/{target}/follow-ups", {**body, "action": "reassign"}, 409)
    response = command(client, f"{ROOT}/{target}/follow-ups", body).json()["current"]
    assert response["summary"]["follow_up"]["overdue"] is False
    assert response["summary"]["review_status"] == "needs_follow_up"
    assert response["content_version"] == 1


def test_cleared_address_can_be_reviewed_as_needing_followup(client):
    target = worker(client)["summary"]["intake_id"]
    command(
        client,
        f"{ROOT}/{target}/addresses/worker_residence/revisions",
        {"expected_version": 1, "address": None},
    )
    current = command(client, f"{ROOT}/{target}/reviews", followup_body(2)).json()["current"]
    assert current["content_version"] == 2
    assert current["summary"]["review_status"] == "needs_follow_up"
    event = client.post(f"{ROOT}/{target}/history/query", json={}).json()["items"][0]["event_id"]
    protected = client.get(f"{ROOT}/{target}/history/{event}/restricted")
    assert protected.status_code == 200, protected.text
    assert protected.json()["reviewed_content"]["addresses"] == {"worker_residence": None}


@pytest.mark.parametrize("surface", ["history", "follow-up-owners"])
def test_long_valid_staff_display_names_survive_history_and_owner_queries(client, surface):
    principal = resolve_staff_principal_for_settings(get_settings())
    name = "Fictional " + "Reviewer" * 20
    assert 100 < len(name) <= 200
    client.app.dependency_overrides[get_staff_directory] = lambda: StaffDirectory(
        (StaffDirectoryEntry(principal.actor_id, name, True, principal.permissions),)
    )
    target = worker(client, complete=False)["summary"]["intake_id"]
    command(client, f"{ROOT}/{target}/reviews", followup_body(1))
    response = client.post(f"{ROOT}/{target}/{surface}/query", json={})
    assert response.status_code == 200, response.text
    key = "actor_display_name" if surface == "history" else "display_name"
    assert response.json()["items"][0][key] == name
