"""Real lock contention for durable linked commands; no mocked persistence."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from time import monotonic, sleep
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from golden_rose.api.dependencies import SystemClock, get_staff_directory
from golden_rose.api.staff.intake_finalization_schemas import (
    FinalizeIntakeRequest,
    LinkIntakeRequest,
)
from golden_rose.api.staff.intake_review_schemas import ReviewIntakeRequest
from golden_rose.application.finalize_intake import execute_new_intake_finalization
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.link_intake import execute_link_intake
from golden_rose.application.review_intake import execute_review
from tests.integration.api.test_intake_review_workflows import ROOT, worker
from tests.integration.test_intake_link_authority import (
    AUTHORITY_TABLES,
    EMPLOYER_TABLES,
    LINKER,
    WORKER_TABLES,
    canonical,
    counts,
    dependencies,
    draft_employer,
    link,
    reference,
    review,
    rows,
)
from tests.integration.test_intake_link_authority import client as client
from tests.integration.test_intake_migrations import migration_database as migration_database


def operation(function, target, request, key=None, **kwargs) -> Callable[..., Any]:
    return partial(
        function,
        principal=LINKER,
        command_id=key or uuid4(),
        intake_id=UUID(target),
        request=request,
        clock=SystemClock(),
        **kwargs,
    )


def link_operation(target, version, party, key=None) -> Callable[..., Any]:
    return operation(
        execute_link_intake,
        target,
        LinkIntakeRequest.model_validate({"expected_version": version, "party": party}),
        key,
    )


def contend(database, target, operations) -> list[dict[str, Any]]:
    """Hold the intake until both independent commands demonstrably wait on locks."""
    tag = "intake-race-" + uuid4().hex

    def submit(command) -> dict[str, Any]:
        with Session(database) as session:
            session.execute(text("SET LOCAL ROLE golden_rose_runtime"))
            session.execute(text("SET LOCAL statement_timeout = '15s'"))
            session.execute(text("SELECT set_config('application_name',:tag,true)"), {"tag": tag})
            try:
                result, replayed = command(session=session)
                return {"result": result, "replayed": replayed}
            except IntakeError as error:
                return {"error": error.code}

    with Session(database) as blocker, ThreadPoolExecutor(max_workers=2) as executor:
        blocker.execute(
            text("SELECT intake_id FROM intakes WHERE intake_id=:target FOR UPDATE"),
            {"target": UUID(target)},
        )
        futures = [executor.submit(submit, command) for command in operations]
        waiting = 0
        try:
            deadline = monotonic() + 8
            while monotonic() < deadline:
                with database.connect() as observer:
                    waiting = observer.scalar(
                        text(
                            "SELECT count(*) FROM pg_stat_activity WHERE application_name=:tag "
                            "AND wait_event_type='Lock'"
                        ),
                        {"tag": tag},
                    )
                if waiting == 2 or any(future.done() for future in futures):
                    break
                sleep(0.01)
        finally:
            # Release before joining, including failed probes; all commands have a timeout.
            blocker.rollback()
        results = [future.result(timeout=20) for future in futures]
    assert waiting == 2, f"Commands did not both reach lock contention: {results}"
    return results


def draft(client, kind) -> str:
    return str(
        worker(client)["summary"]["intake_id"]
        if kind == "worker"
        else draft_employer(client, "business")
    )


@pytest.mark.parametrize("kind", ["worker", "business"])
@pytest.mark.parametrize("same_key", [True, False])
def test_competing_links_write_one_version_and_one_authority_group(
    client, migration_database, kind, same_key
):
    first = canonical(client, kind)
    second = first if same_key else canonical(client, kind)
    party = "worker" if kind == "worker" else "employer"
    target = draft(client, kind)
    before = counts(migration_database, AUTHORITY_TABLES)
    canonical_before = {
        table: rows(migration_database, table) for table in (*WORKER_TABLES, *EMPLOYER_TABLES)
    }
    key = uuid4()
    results = contend(
        migration_database,
        target,
        [
            link_operation(target, 1, reference(first[party]), key),
            link_operation(target, 1, reference(second[party]), key if same_key else uuid4()),
        ],
    )
    successes = [r for r in results if "result" in r]
    if same_key:
        assert len(successes) == 2
        assert sorted(r["replayed"] for r in successes) == [False, True]
        assert successes[0]["result"] == successes[1]["result"]
    else:
        assert len(successes) == 1
        assert [r["error"] for r in results if "error" in r] == ["version_conflict"]
    selected = first if "result" in results[0] else second
    assert dependencies(migration_database, target)[party] == reference(selected[party])
    assert counts(migration_database, AUTHORITY_TABLES) == {t: n + 1 for t, n in before.items()}
    assert {t: rows(migration_database, t) for t in canonical_before} == canonical_before
    current = client.get(f"{ROOT}/{target}").json()
    assert current["summary"]["version"] == current["content_version"] == 2


@pytest.mark.parametrize("kind", ["worker", "business"])
@pytest.mark.parametrize("same_key", [True, False])
def test_competing_linked_finalizations_create_only_one_output_set(
    client, migration_database, kind, same_key
):
    refs = canonical(client, kind)
    party = "worker" if kind == "worker" else "employer"
    target = draft(client, kind)
    children = (
        {}
        if kind == "worker"
        else {
            "contact": reference(refs["contact"]),
            "worksite": reference(refs["worksite"]),
            "business_address": reference(refs["business_address"]),
        }
    )
    link(migration_database, target, 1, reference(refs[party]), **children)
    body = review(client, target, 2)
    before = counts(migration_database, (*AUTHORITY_TABLES, *WORKER_TABLES, *EMPLOYER_TABLES))
    key = uuid4()
    results = contend(
        migration_database,
        target,
        [
            operation(
                execute_new_intake_finalization,
                target,
                FinalizeIntakeRequest.model_validate(body),
                k,
            )
            for k in (key, key if same_key else uuid4())
        ],
    )
    successes = [r for r in results if "result" in r]
    if same_key:
        assert len(successes) == 2
        assert sorted(r["replayed"] for r in successes) == [False, True]
        assert successes[0]["result"]["finalization"] == successes[1]["result"]["finalization"]
    else:
        assert len(successes) == 1
        assert [r["error"] for r in results if "error" in r] == ["already_finalized"]
    expected = dict(before)
    expected["command_receipts"] += 1
    for table in ("command_results", "audit_events"):
        expected[table] += 1 if kind == "worker" else 2
    expected["staffing_requests"] += int(kind != "worker")
    assert counts(migration_database, expected) == expected
    current = client.get(f"{ROOT}/{target}").json()
    assert current["summary"]["lifecycle"] == "finalized"
    assert current["finalization"][party] == {**reference(refs[party]), "disposition": "reused"}
    assert (
        len(
            [
                r
                for r in rows(migration_database, "intake_finalizations")
                if str(r["intake_id"]) == target
            ]
        )
        == 1
    )


def test_review_and_link_replacement_cannot_share_an_expected_version(client, migration_database):
    first, second = canonical(client), canonical(client)
    target = draft(client, "worker")
    link(migration_database, target, 1, reference(first["worker"]))
    results = contend(
        migration_database,
        target,
        [
            operation(
                execute_review,
                target,
                ReviewIntakeRequest(expected_version=2, outcome="intake_reviewed"),
                directory=client.app.dependency_overrides[get_staff_directory](),
            ),
            link_operation(target, 2, reference(second["worker"])),
        ],
    )
    assert len([r for r in results if "result" in r]) == 1
    assert [r["error"] for r in results if "error" in r] == ["version_conflict"]
    current = client.get(f"{ROOT}/{target}").json()
    assert current["summary"]["version"] == 3
    if "result" in results[0]:
        assert dependencies(migration_database, target)["worker"] == reference(first["worker"])
        payload = next(
            r
            for r in rows(migration_database, "intake_review_payloads")
            if str(r["review_id"]) == current["latest_review"]["review_id"]
        )
        assert payload["dependency_refs"] == dependencies(migration_database, target)
        assert current["content_version"] == 2
    else:
        assert dependencies(migration_database, target)["worker"] == reference(second["worker"])
        assert current.get("latest_review") is None
        assert not any(
            str(row["intake_id"]) == target for row in rows(migration_database, "intake_reviews")
        )
        assert current["content_version"] == 3


def test_finalization_and_unlink_cannot_commit_incompatible_results(client, migration_database):
    refs = canonical(client)
    target = draft(client, "worker")
    link(migration_database, target, 1, reference(refs["worker"]))
    body = review(client, target, 2)
    before = {table: rows(migration_database, table) for table in WORKER_TABLES}
    results = contend(
        migration_database,
        target,
        [
            operation(
                execute_new_intake_finalization, target, FinalizeIntakeRequest.model_validate(body)
            ),
            link_operation(target, 3, None),
        ],
    )
    assert len([r for r in results if "result" in r]) == 1
    current = client.get(f"{ROOT}/{target}").json()
    assert current["summary"]["version"] == 4
    if "result" in results[0]:
        assert results[1]["error"] == "already_finalized"
        assert current["summary"]["lifecycle"] == "finalized"
        assert dependencies(migration_database, target)["worker"] == reference(refs["worker"])
    else:
        assert results[0]["error"] == "version_conflict"
        assert current["summary"]["lifecycle"] == "draft"
        assert current.get("finalization") is None
        assert not any(
            str(row["intake_id"]) == target
            for row in rows(migration_database, "intake_finalizations")
        )
        assert dependencies(migration_database, target) == {}
    assert {table: rows(migration_database, table) for table in before} == before
