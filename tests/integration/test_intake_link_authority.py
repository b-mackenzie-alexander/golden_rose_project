"""PostgreSQL successor authority, durable linking, and mixed-output acceptance.

Link commands are invoked directly until a route exists. All canonical references
come from API finalizations; these tests require the disposable database fixture.
"""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager, nullcontext
from dataclasses import replace
from typing import Any
from uuid import UUID, uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from golden_rose.api.dependencies import SystemClock, get_staff_directory, get_staff_principal
from golden_rose.api.staff.intake_finalization_schemas import (
    FinalizeIntakeRequest,
    LinkIntakeRequest,
)
from golden_rose.application import finalize_intake, review_intake
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.intake_workflow_common import begin_command, write_authority
from golden_rose.application.link_intake import execute_link_intake
from golden_rose.auth.staff_directory import StaffDirectory, StaffDirectoryEntry
from golden_rose.main import create_app
from golden_rose.persistence import employer_intake_outputs
from golden_rose.persistence.intake_links import get_link_dependencies
from golden_rose.persistence.intakes import address_complete
from tests.integration.api.test_employer_finalizations import reviewed_employer
from tests.integration.api.test_intake_finalizations import reviewed_worker
from tests.integration.api.test_intake_review_workflows import ROOT, command, worker
from tests.integration.test_intake_finalization import FINALIZER
from tests.integration.test_intake_migrations import migrate
from tests.integration.test_intake_migrations import migration_database as migration_database
from tests.unit.test_employer_finalization_outputs import PARTY, WORKSITE, content

REVISION = "0008c_intake_link_authority"
PREDECESSOR = "0008b_intake_link_storage"
LINKER = replace(
    FINALIZER,
    permissions=FINALIZER.permissions
    | {
        "intake:link",
        "worker:read",
        "worker_contact:read",
        "employer:read",
        "employer:draft:revise",
        "employer_contact:read",
        "employer_contact:details:read",
        "worksite:read",
    },
)
WORKER_TABLES = (
    "workers",
    "worker_contacts",
    "worker_residences",
    "worker_preferences",
    "worker_interest_selections",
)
EMPLOYER_TABLES = (
    "employers",
    "employer_contacts",
    "employer_contact_details",
    "employer_addresses",
    "worksites",
    "staffing_requests",
)
AUTHORITY_TABLES = ("command_receipts", "command_results", "audit_events")


@contextmanager
def api(database) -> Iterator[Any]:
    app = create_app(engine_factory=lambda: database)
    app.dependency_overrides[get_staff_principal] = lambda: LINKER
    directory = StaffDirectory(
        (StaffDirectoryEntry(LINKER.actor_id, "Fictional Link Reviewer", True, LINKER.permissions),)
    )
    app.dependency_overrides[get_staff_directory] = lambda: directory
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
def client(migration_database) -> Iterator[Any]:
    migrate(migration_database, "head")
    with api(migration_database) as client:
        yield client


def canonical(client, kind="worker") -> dict[str, Any]:
    target, body = reviewed_worker(client) if kind == "worker" else reviewed_employer(client, kind)
    return dict(command(client, f"{ROOT}/{target}/finalizations", body, 201).json()["finalization"])


def reference(value) -> dict[str, Any]:
    return {"id": value["id"], "version": value["version"]}


def link(database, target, version, party, *, key=None, **children) -> tuple[dict[str, Any], bool]:
    with Session(database) as session:
        return execute_link_intake(
            session=session,
            principal=LINKER,
            command_id=key or uuid4(),
            intake_id=UUID(target),
            clock=SystemClock(),
            request=LinkIntakeRequest.model_validate(
                {"expected_version": version, "party": party, **children}
            ),
        )


def rows(database, table) -> Sequence[Any]:
    with database.connect() as connection:
        return list(
            connection.execute(text(f"SELECT * FROM {table} ORDER BY to_jsonb({table})::text"))
            .mappings()
            .all()
        )


def counts(database, tables) -> dict[str, Any]:
    return {table: len(rows(database, table)) for table in tables}


def dependencies(database, target) -> dict[str, Any]:
    with Session(database) as session:
        return get_link_dependencies(session, UUID(target))


def draft_employer(client, kind) -> Any:
    return command(
        client,
        ROOT,
        {
            "kind": "employer",
            "content": {
                **content(kind),
                "display_name": "Fictional Candidate Preserved",
                "party_address": PARTY,
                "worksite_address": WORKSITE,
            },
        },
        201,
    ).json()["current"]["summary"]["intake_id"]


def review(client, target, version) -> dict[str, Any]:
    current = command(
        client,
        f"{ROOT}/{target}/reviews",
        {"expected_version": version, "outcome": "intake_reviewed"},
    ).json()["current"]
    return {"expected_version": version + 1, "review_id": current["latest_review"]["review_id"]}


def test_worker_link_replace_unlink_preserves_candidate_and_original_retry(
    client, migration_database
):
    first, second = canonical(client), canonical(client)
    draft = worker(client)
    target = draft["summary"]["intake_id"]
    original_content = next(
        r["content"] for r in rows(migration_database, "intakes") if str(r["intake_id"]) == target
    )
    original_addresses = rows(migration_database, "intake_addresses")
    key = uuid4()
    result, replayed = link(migration_database, target, 1, reference(first["worker"]), key=key)
    assert (
        not replayed
        and result["result_record_version"] == result["current"]["content_version"] == 2
    )
    assert dependencies(migration_database, target)["worker"] == reference(first["worker"])
    body = review(client, target, 2)
    link(migration_database, target, 3, reference(second["worker"]))
    assert dependencies(migration_database, target)["worker"] == reference(second["worker"])
    stale = command(client, f"{ROOT}/{target}/finalizations", {**body, "expected_version": 4}, 409)
    assert stale.json()["code"] == "review_required"
    result, _ = link(migration_database, target, 4, None)
    assert (
        result["current"]["summary"]["version"] == 5 and result["current"]["content_version"] == 4
    )
    assert dependencies(migration_database, target) == {}
    assert len(rows(migration_database, "intake_links")) == 1
    before = counts(migration_database, AUTHORITY_TABLES)
    replay, replayed = link(
        migration_database,
        target,
        1,
        reference(first["worker"]),
        key=key,
    )
    assert replayed and replay["result_record_version"] == 2
    assert replay["current"]["summary"]["version"] == 5
    assert counts(migration_database, AUTHORITY_TABLES) == before
    row = next(r for r in rows(migration_database, "intakes") if str(r["intake_id"]) == target)
    assert row["content"] == original_content
    assert rows(migration_database, "intake_addresses") == original_addresses
    assert dependencies(migration_database, target) == {}


def test_worker_full_reuse_review_snapshot_and_finalization_create_no_canonical_rows(
    client,
    migration_database,
):
    refs = canonical(client)
    target = worker(client, complete=False)["summary"]["intake_id"]
    link(migration_database, target, 1, reference(refs["worker"]))
    body = review(client, target, 2)
    payload = next(
        r
        for r in rows(migration_database, "intake_review_payloads")
        if str(r["review_id"]) == body["review_id"]
    )
    assert payload["dependency_refs"] == dependencies(migration_database, target)
    assert payload["reviewed_content"]["content"]["phone"] == "202-555-0151"
    before = {table: rows(migration_database, table) for table in WORKER_TABLES}
    key = uuid4()
    result = command(client, f"{ROOT}/{target}/finalizations", body, 201, key).json()
    for name in ("worker", "contact", "residence", "preferences"):
        assert reference(result["finalization"][name]) == reference(refs[name])
        assert result["finalization"][name]["disposition"] == "reused"
    assert {table: rows(migration_database, table) for table in WORKER_TABLES} == before
    outputs = [r for r in rows(migration_database, "command_results") if r["command_id"] == key]
    assert [r["entity_type"] for r in outputs] == ["intake"]
    replay = command(client, f"{ROOT}/{target}/finalizations", body, key=key)
    assert replay.headers["idempotency-replayed"] == "true"
    assert replay.json()["finalization"] == result["finalization"]


@pytest.mark.parametrize("kind", ["household", "business"])
@pytest.mark.parametrize("reuse_worksite", [True, False])
def test_employer_all_or_partial_reuse_creates_only_missing_outputs(
    client,
    migration_database,
    kind,
    reuse_worksite,
):
    refs = canonical(client, kind)
    target = draft_employer(client, kind)
    children = {"contact": reference(refs["contact"])}
    if reuse_worksite:
        children["worksite"] = reference(refs["worksite"])
    if kind == "business":
        children["business_address"] = reference(refs["business_address"])
    link(migration_database, target, 1, reference(refs["employer"]), **children)
    body = review(client, target, 2)
    before = counts(migration_database, EMPLOYER_TABLES)
    key = uuid4()
    result = command(client, f"{ROOT}/{target}/finalizations", body, 201, key).json()[
        "finalization"
    ]
    expected = {**before, "staffing_requests": before["staffing_requests"] + 1}
    expected["worksites"] += int(not reuse_worksite)
    assert counts(migration_database, EMPLOYER_TABLES) == expected
    for name in ("employer", "contact", "contact_details", "business_address", "worksite"):
        if refs[name] is None:
            assert result[name] is None
        elif name != "worksite" or reuse_worksite:
            assert reference(result[name]) == reference(refs[name])
            assert result[name]["disposition"] == "reused"
        else:
            assert result[name]["id"] != refs[name]["id"]
            assert result[name]["disposition"] == "created"
    outputs = {
        r["entity_type"]
        for r in rows(migration_database, "command_results")
        if r["command_id"] == key
    }
    assert outputs == ({"intake", "staffing_request"} | (set() if reuse_worksite else {"worksite"}))
    request = next(
        r
        for r in rows(migration_database, "staffing_requests")
        if str(r["staffing_request_id"]) == result["request"]["id"]
    )
    assert str(request["employer_id"]) == refs["employer"]["id"]
    assert str(request["employer_contact_id"]) == refs["contact"]["id"]
    assert str(request["worksite_id"]) == result["worksite"]["id"]


@pytest.mark.parametrize("child", ["contact", "worksite", "business_address"])
def test_cross_parent_employer_selection_rolls_back(client, migration_database, child):
    first, second = canonical(client, "business"), canonical(client, "business")
    target = draft_employer(client, "business")
    before = counts(migration_database, AUTHORITY_TABLES)
    with pytest.raises(IntakeError, match="not_found"):
        link(
            migration_database,
            target,
            1,
            reference(first["employer"]),
            **{child: reference(second[child])},
        )
    assert dependencies(migration_database, target) == {}
    assert counts(migration_database, AUTHORITY_TABLES) == before
    assert client.get(f"{ROOT}/{target}").json()["summary"]["version"] == 1


@pytest.mark.parametrize("kind", ["worker", "business"])
def test_stale_canonical_version_rejects_link_without_authority(client, migration_database, kind):
    refs = canonical(client, kind)
    party = "worker" if kind == "worker" else "employer"
    target = (
        worker(client)["summary"]["intake_id"] if kind == "worker" else draft_employer(client, kind)
    )
    before = counts(migration_database, AUTHORITY_TABLES)
    with pytest.raises(IntakeError, match="dependency_changed"):
        link(migration_database, target, 1, {**reference(refs[party]), "version": 2})
    assert dependencies(migration_database, target) == {}
    assert counts(migration_database, AUTHORITY_TABLES) == before


def test_canonical_revision_after_review_blocks_finalization(client, migration_database):
    refs = canonical(client, "business")
    target = draft_employer(client, "business")
    link(migration_database, target, 1, reference(refs["employer"]))
    body = review(client, target, 2)
    response = client.post(
        f"/api/staff/v1/employers/{refs['employer']['id']}/revisions",
        headers={"Idempotency-Key": str(uuid4())},
        json={
            "expected_version": refs["employer"]["version"],
            "employer_type": "business",
            "display_name": "Fictional Canonical Revision",
        },
    )
    assert response.status_code == 200, response.text
    before = counts(migration_database, (*AUTHORITY_TABLES, *EMPLOYER_TABLES))
    response = command(client, f"{ROOT}/{target}/finalizations", body, 409)
    assert response.json()["code"] == "dependency_changed"
    assert counts(migration_database, (*AUTHORITY_TABLES, *EMPLOYER_TABLES)) == before
    assert dependencies(migration_database, target)["employer"] == reference(refs["employer"])
    assert client.get(f"{ROOT}/{target}").json()["summary"]["lifecycle"] == "draft"


def test_parent_version_refresh_preserves_children_and_requires_new_review(
    client, migration_database
):
    refs = canonical(client, "business")
    target = draft_employer(client, "business")
    children = {name: reference(refs[name]) for name in ("contact", "worksite", "business_address")}
    link(migration_database, target, 1, reference(refs["employer"]), **children)
    old_review = review(client, target, 2)
    old_dependencies = dependencies(migration_database, target)
    old_children = rows(migration_database, "intake_links")
    old_payloads = rows(migration_database, "intake_review_payloads")
    original_content = next(
        r["content"] for r in rows(migration_database, "intakes") if str(r["intake_id"]) == target
    )
    response = client.post(
        f"/api/staff/v1/employers/{refs['employer']['id']}/revisions",
        headers={"Idempotency-Key": str(uuid4())},
        json={
            "expected_version": 1,
            "employer_type": "business",
            "display_name": "Fictional Refreshed Employer",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["version"] == 2
    refreshed = {"id": refs["employer"]["id"], "version": 2}
    result, replayed = link(migration_database, target, 3, refreshed, **children)
    assert not replayed
    assert result["result_record_version"] == result["current"]["summary"]["version"] == 4
    assert result["current"]["content_version"] == 3
    assert dependencies(migration_database, target) == {
        **old_dependencies,
        "employer": refreshed,
    }
    assert rows(migration_database, "intake_links") == old_children
    assert rows(migration_database, "intake_review_payloads") == old_payloads
    current = client.get(f"{ROOT}/{target}")
    assert current.status_code == 200, current.text
    assert current.json()["summary"]["review_status"] == "stale"
    assert current.json()["latest_review"]["review_id"] == old_review["review_id"]
    rejected = command(
        client,
        f"{ROOT}/{target}/finalizations",
        {**old_review, "expected_version": 4},
        409,
    )
    assert rejected.json()["code"] == "review_required"
    body = review(client, target, 4)
    payload = next(
        r
        for r in rows(migration_database, "intake_review_payloads")
        if str(r["review_id"]) == body["review_id"]
    )
    assert payload["dependency_refs"] == {**old_dependencies, "employer": refreshed}
    assert payload["reviewed_content"]["content"]["display_name"] == "Fictional Refreshed Employer"
    before = {table: rows(migration_database, table) for table in EMPLOYER_TABLES}
    key = uuid4()
    finalized = command(client, f"{ROOT}/{target}/finalizations", body, 201, key).json()
    assert finalized["result_record_version"] == 6
    assert finalized["finalization"]["employer"] == {**refreshed, "disposition": "reused"}
    for name in ("contact", "contact_details", "worksite", "business_address"):
        assert finalized["finalization"][name] == {**reference(refs[name]), "disposition": "reused"}
    assert finalized["finalization"]["request"]["disposition"] == "created"
    for table in EMPLOYER_TABLES:
        if table == "staffing_requests":
            assert len(rows(migration_database, table)) == len(before[table]) + 1
        else:
            assert rows(migration_database, table) == before[table]
    assert {
        r["entity_type"]
        for r in rows(migration_database, "command_results")
        if r["command_id"] == key
    } == {"intake", "staffing_request"}
    row = next(r for r in rows(migration_database, "intakes") if str(r["intake_id"]) == target)
    assert row["content"] == original_content and row["content_version"] == 3


@pytest.mark.parametrize(
    "savepoint,earlyflush",
    [(False, False), (True, False), (False, True)],
    ids=["ordinary", "savepoint", "early-flush"],
)
def test_child_clear_then_restore_with_one_link_command_rejects(
    client, migration_database, savepoint, earlyflush
):
    refs = canonical(client, "business")
    target = draft_employer(client, "business")
    link(
        migration_database,
        target,
        1,
        reference(refs["employer"]),
        worksite=reference(refs["worksite"]),
    )
    original_dependencies = dependencies(migration_database, target)
    before = {
        table: rows(migration_database, table)
        for table in (*AUTHORITY_TABLES, "intakes", "intake_links")
    }
    key, now = uuid4(), SystemClock().now()
    with Session(migration_database) as session:
        session.execute(text("SET LOCAL ROLE golden_rose_runtime"))
        fingerprint, receipt = begin_command(
            session,
            LINKER,
            key,
            "link_intake",
            UUID(target),
            LinkIntakeRequest.model_validate(
                {
                    "expected_version": 2,
                    "party": reference(refs["employer"]),
                    "worksite": reference(refs["worksite"]),
                }
            ).model_dump(mode="json"),
        )
        assert receipt is None
        write_authority(
            session,
            principal=LINKER,
            command_id=key,
            command_type="link_intake",
            fingerprint=fingerprint,
            entity_type="intake",
            entity_id=UUID(target),
            previous_version=2,
            event_type="intake.linked",
            event_id=uuid4(),
            now=now,
            changed=["links"],
        )
        session.execute(
            text(
                "UPDATE intakes SET version=version+1,content_version=content_version+1,"
                "updated_at=:now,updated_by=:actor WHERE intake_id=:intake"
            ),
            {"now": now, "actor": LINKER.actor_id, "intake": UUID(target)},
        )
        # Release (do not roll back) the savepoint so its deferred event survives.
        with session.begin_nested() if savepoint else nullcontext():
            session.execute(
                text(
                    "UPDATE intake_links SET worksite_id=NULL,worksite_version=NULL "
                    "WHERE intake_id=:intake"
                ),
                {"intake": UUID(target)},
            )
            assert "worksite" not in get_link_dependencies(session, UUID(target))
        assert session.execute(
            text("SELECT version,content_version FROM intakes WHERE intake_id=:intake"),
            {"intake": UUID(target)},
        ).one() == (3, 3)
        for table in AUTHORITY_TABLES:
            assert (
                session.scalar(
                    text(f"SELECT count(*) FROM {table} WHERE command_id=:command"),
                    {"command": key},
                )
                == 1
            )
        if earlyflush:
            # This must succeed so the later rejection tests the BEFORE UPDATE guard.
            session.execute(text("SET CONSTRAINTS guard_intake_links IMMEDIATE"))
        reached_commit = False
        with pytest.raises(IntegrityError) as caught:
            session.execute(
                text(
                    "UPDATE intake_links SET worksite_id=:worksite,worksite_version=:version "
                    "WHERE intake_id=:intake"
                ),
                {
                    "worksite": UUID(refs["worksite"]["id"]),
                    "version": refs["worksite"]["version"],
                    "intake": UUID(target),
                },
            )
            assert get_link_dependencies(session, UUID(target)) == original_dependencies
            reached_commit = True
            session.commit()
        assert reached_commit is savepoint
        assert isinstance(caught.value.orig, psycopg.Error)
        assert caught.value.orig.sqlstate == "23514"
        assert "multiple link replacements in one transaction" in str(caught.value.orig)
        session.rollback()
    assert {table: rows(migration_database, table) for table in before} == before


def test_orphan_link_authority_without_intake_update_rejects_at_commit(client, migration_database):
    target = UUID(worker(client)["summary"]["intake_id"])
    before = {
        table: rows(migration_database, table)
        for table in (*AUTHORITY_TABLES, "intakes", "intake_links")
    }
    key = uuid4()
    with Session(migration_database) as session:
        session.execute(text("SET LOCAL ROLE golden_rose_runtime"))
        fingerprint, receipt = begin_command(
            session,
            LINKER,
            key,
            "link_intake",
            target,
            {"expected_version": 1, "party": None},
        )
        assert receipt is None
        write_authority(
            session,
            principal=LINKER,
            command_id=key,
            command_type="link_intake",
            fingerprint=fingerprint,
            entity_type="intake",
            entity_id=target,
            previous_version=1,
            event_type="intake.linked",
            event_id=uuid4(),
            now=SystemClock().now(),
            changed=["links"],
        )
        # All three authority rows exist in this transaction, but no intake was updated.
        for table in AUTHORITY_TABLES:
            assert (
                session.scalar(
                    text(f"SELECT count(*) FROM {table} WHERE command_id=:command"),
                    {"command": key},
                )
                == 1
            )
        with pytest.raises(IntegrityError) as caught:
            session.commit()
        assert isinstance(caught.value.orig, psycopg.Error)
        assert caught.value.orig.sqlstate == "23514"
        session.rollback()
    assert {table: rows(migration_database, table) for table in before} == before


def test_household_reuse_of_business_contact_without_address_fails_database_guard(
    client,
    migration_database,
    monkeypatch,
):
    refs = canonical(client, "business")
    response = client.post(
        f"/api/staff/v1/employers/{refs['employer']['id']}/revisions",
        headers={"Idempotency-Key": str(uuid4())},
        json={
            "expected_version": 1,
            "employer_type": "household",
            "display_name": "Fictional Converted Household",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["version"] == 2
    target = draft_employer(client, "household")
    link(
        migration_database,
        target,
        1,
        {"id": refs["employer"]["id"], "version": 2},
        contact=reference(refs["contact"]),
        worksite=reference(refs["worksite"]),
    )
    rejected = command(
        client,
        f"{ROOT}/{target}/reviews",
        {"expected_version": 2, "outcome": "intake_reviewed"},
        422,
    )
    assert "party_address" in rejected.json()["missing_fields"]
    # Bypass only application completeness; the real linked snapshot stays empty.
    monkeypatch.setattr(review_intake, "missing_fields", lambda *args, **kwargs: [])
    monkeypatch.setattr(finalize_intake, "missing_fields", lambda *args, **kwargs: [])
    body = review(client, target, 2)
    payload = next(
        r
        for r in rows(migration_database, "intake_review_payloads")
        if str(r["review_id"]) == body["review_id"]
    )
    assert payload["dependency_refs"] == dependencies(migration_database, target)
    assert payload["reviewed_content"]["addresses"]["party_address"] == {}
    original_complete = address_complete
    assert not original_complete({})
    bypassed_addresses = []

    def admit_empty_address(address) -> Any:
        if address == {}:
            bypassed_addresses.append(dict(address))
            return True
        return original_complete(address)

    # Let the unchanged empty canonical address pass the writer's second check.
    monkeypatch.setattr(employer_intake_outputs, "address_complete", admit_empty_address)
    before = {
        table: rows(migration_database, table)
        for table in (
            *AUTHORITY_TABLES,
            *EMPLOYER_TABLES,
            "intakes",
            "intake_links",
            "intake_finalizations",
            "intake_review_payloads",
        )
    }
    with Session(migration_database) as session, pytest.raises(IntakeError) as caught:
        finalize_intake.execute_new_intake_finalization(
            session=session,
            principal=LINKER,
            command_id=uuid4(),
            intake_id=UUID(target),
            request=FinalizeIntakeRequest.model_validate(body),
            clock=SystemClock(),
        )
    assert caught.value.code == "persistence_unavailable" and caught.value.status == 503
    assert isinstance(caught.value.__cause__, IntegrityError)
    assert "incomplete household output address" in str(caught.value.__cause__.orig)
    assert bypassed_addresses == [{}]
    assert {table: rows(migration_database, table) for table in before} == before
    current = client.get(f"{ROOT}/{target}")
    assert current.status_code == 200, current.text
    assert current.json()["summary"]["lifecycle"] == "draft"
    assert current.json()["summary"]["version"] == 3


def test_raw_link_row_noop_update_rejects_and_rolls_back(client, migration_database):
    refs = canonical(client, "business")
    target = draft_employer(client, "business")
    link(
        migration_database,
        target,
        1,
        reference(refs["employer"]),
        worksite=reference(refs["worksite"]),
    )
    before = {
        table: rows(migration_database, table)
        for table in (*AUTHORITY_TABLES, "intakes", "intake_links")
    }
    with pytest.raises(IntegrityError), migration_database.begin() as connection:
        connection.execute(text("SET LOCAL ROLE golden_rose_runtime"))
        connection.execute(
            text("UPDATE intake_links SET worksite_id=worksite_id WHERE intake_id=:intake"),
            {"intake": UUID(target)},
        )
    assert {table: rows(migration_database, table) for table in before} == before


def test_forged_standalone_child_mutation_rolls_back_at_commit(client, migration_database):
    refs = canonical(client, "business")
    target = draft_employer(client, "business")
    link(migration_database, target, 1, reference(refs["employer"]))
    before = rows(migration_database, "intake_links")
    authority = counts(migration_database, AUTHORITY_TABLES)
    with pytest.raises(IntegrityError), migration_database.begin() as connection:
        connection.execute(text("SET LOCAL ROLE golden_rose_runtime"))
        # A valid same-parent child still needs a link command and intake version advance.
        connection.execute(
            text(
                "UPDATE intake_links SET worksite_id=:worksite,worksite_version=:version "
                "WHERE intake_id=:intake"
            ),
            {
                "worksite": UUID(refs["worksite"]["id"]),
                "version": refs["worksite"]["version"],
                "intake": UUID(target),
            },
        )
    assert rows(migration_database, "intake_links") == before
    assert counts(migration_database, AUTHORITY_TABLES) == authority


@pytest.mark.parametrize("unlink", [False, True])
def test_successor_downgrade_refuses_link_history_before_ddl(client, migration_database, unlink):
    refs = canonical(client)
    target = worker(client)["summary"]["intake_id"]
    link(migration_database, target, 1, reference(refs["worker"]))
    if unlink:
        link(migration_database, target, 2, None)
        assert dependencies(migration_database, target) == {}
    before = {
        table: rows(migration_database, table)
        for table in (*AUTHORITY_TABLES, "intakes", "intake_links")
    }
    with pytest.raises(RuntimeError, match="before DDL"):
        migrate(migration_database, PREDECESSOR, downgrade=True)
    assert (
        rows(migration_database, "alembic_version")[0]["version_num"] == "0009a_canonical_reviews"
    )
    assert {table: rows(migration_database, table) for table in before} == before
    with migration_database.connect() as connection:
        assert connection.scalar(
            text(
                "SELECT has_column_privilege('golden_rose_runtime','intakes','worker_id','UPDATE')"
            )
        )


def test_populated_predecessor_upgrade_and_safe_downgrade_preserve_exact_rows(migration_database):
    migrate(migration_database, PREDECESSOR)
    with api(migration_database) as client:
        for kind in ("worker", "household", "business"):
            canonical(client, kind)
        tables = (
            *AUTHORITY_TABLES,
            *WORKER_TABLES,
            *EMPLOYER_TABLES,
            "intakes",
            "intake_addresses",
            "intake_reviews",
            "intake_review_payloads",
            "intake_finalizations",
        )
        before = {table: rows(migration_database, table) for table in tables}
        migrate(migration_database, REVISION)
        assert {table: rows(migration_database, table) for table in tables} == before
        migrate(migration_database, PREDECESSOR, downgrade=True)
        assert {table: rows(migration_database, table) for table in tables} == before


def test_successor_grants_only_exact_reference_update_columns(client, migration_database):
    expected = {
        "intakes": {
            "content",
            "version",
            "content_version",
            "updated_at",
            "updated_by",
            "lifecycle_status",
            "worker_id",
            "worker_version",
            "employer_id",
            "employer_version",
        },
        "intake_links": {"worker_id", "employer_id"}
        | {
            f"{name}_{suffix}"
            for name in (
                "worker_contact",
                "worker_residence",
                "worker_preferences",
                "employer_contact",
                "employer_contact_details",
                "worksite",
                "employer_address",
            )
            for suffix in ("id", "version")
        },
    }
    with migration_database.connect() as connection:
        for table, columns in expected.items():
            actual = (
                connection.execute(
                    text(
                        "SELECT attname FROM pg_attribute WHERE attrelid=CAST(:table AS regclass) "
                        "AND attnum>0 AND NOT attisdropped AND "
                        "has_column_privilege('golden_rose_runtime',attrelid,attname,'UPDATE')"
                    ),
                    {"table": table},
                )
                .scalars()
                .all()
            )
            assert set(actual) == columns
            for privilege in ("UPDATE", "DELETE", "TRUNCATE", "TRIGGER", "REFERENCES"):
                assert not connection.scalar(
                    text("SELECT has_table_privilege('golden_rose_runtime',:table,:privilege)"),
                    {"table": table, "privilege": privilege},
                )
            for privilege in ("SELECT", "INSERT"):
                assert connection.scalar(
                    text("SELECT has_table_privilege('golden_rose_runtime',:table,:privilege)"),
                    {"table": table, "privilege": privilege},
                )
