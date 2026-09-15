"""Force both sides of canonical Employer revision/finalization ordering."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Event
from time import monotonic, sleep
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from golden_rose.api.dependencies import SystemClock, get_staff_directory
from golden_rose.api.staff.intake_finalization_schemas import FinalizeIntakeRequest
from golden_rose.api.staff.intake_review_schemas import ReviewIntakeRequest
from golden_rose.application.finalize_intake import execute_new_intake_finalization
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.review_intake import execute_review
from golden_rose.application.revise_draft_employer import revise_draft_employer
from tests.integration.test_intake_link_authority import (
    AUTHORITY_TABLES,
    EMPLOYER_TABLES,
    LINKER,
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
from tests.integration.test_linked_intake_concurrency import link_operation, operation


def commit_before_waiter(database, first, second) -> tuple[dict[str, Any], dict[str, Any]]:
    """Pause a real transaction at commit and prove the second waits on its locks."""
    ready, release = Event(), Event()
    tag = "parent-race-" + uuid4().hex
    blocker_pid = []

    class HeldSession(Session):
        def commit(self) -> None:
            self.flush()
            ready.set()
            if not release.wait(timeout=12):
                raise AssertionError("Timed out waiting to release canonical parent transaction")
            super().commit()

    def submit(command, held) -> dict[str, Any]:
        with HeldSession(database) if held else Session(database) as session:
            session.execute(text("SET LOCAL ROLE golden_rose_runtime"))
            session.execute(text("SET LOCAL statement_timeout = '15s'"))
            if held:
                blocker_pid.append(session.scalar(text("SELECT pg_backend_pid()")))
            else:
                session.execute(
                    text("SELECT set_config('application_name',:tag,true)"), {"tag": tag}
                )
            try:
                return {"value": command(session=session)}
            except IntakeError as error:
                return {"error": error.code}

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(submit, first, True)
        blocked = False
        try:
            assert ready.wait(timeout=8), "First command failed to reach its commit boundary"
            second_future = executor.submit(submit, second, False)
            deadline = monotonic() + 8
            while monotonic() < deadline:
                with database.connect() as observer:
                    blocked = observer.scalar(
                        text(
                            "SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
                            "WHERE application_name=:tag AND wait_event_type='Lock' "
                            "AND :blocker = ANY(pg_blocking_pids(pid)))"
                        ),
                        {"tag": tag, "blocker": blocker_pid[0]},
                    )
                if blocked or second_future.done():
                    break
                sleep(0.01)
        finally:
            release.set()
        results = first_future.result(timeout=20), second_future.result(timeout=20)
    assert blocked, f"Second command never waited on the first transaction: {results}"
    return results


def revision(refs, kind="business") -> Callable[..., Any]:
    return partial(
        revise_draft_employer,
        principal=LINKER,
        command_id=uuid4(),
        employer_id=UUID(refs["employer"]["id"]),
        expected_version=1,
        employer_type=kind,
        display_name="Fictional Concurrent Employer Revision",
        clock=SystemClock(),
    )


@pytest.mark.parametrize("command_kind", ["link", "review", "finalize"])
def test_revision_commits_before_waiting_intake_command_rechecks_dependencies(
    client, migration_database, command_kind
):
    refs = canonical(client, "business")
    target = draft_employer(client, "business")
    if command_kind == "link":
        waiting = link_operation(target, 1, reference(refs["employer"]))
    else:
        link(migration_database, target, 1, reference(refs["employer"]))
        if command_kind == "review":
            waiting = operation(
                execute_review,
                target,
                ReviewIntakeRequest(expected_version=2, outcome="intake_reviewed"),
                directory=client.app.dependency_overrides[get_staff_directory](),
            )
        else:
            body = review(client, target, 2)
            waiting = operation(
                execute_new_intake_finalization, target, FinalizeIntakeRequest.model_validate(body)
            )
    unchanged_tables = (
        *(t for t in EMPLOYER_TABLES if t != "employers"),
        "intakes",
        "intake_links",
        "intake_reviews",
        "intake_review_payloads",
        "intake_finalizations",
    )
    before = {t: rows(migration_database, t) for t in unchanged_tables}
    authority_before = counts(migration_database, AUTHORITY_TABLES)
    committed, rejected = commit_before_waiter(migration_database, revision(refs), waiting)
    assert committed["value"].result_record_version == 2
    assert rejected == {"error": "dependency_changed"}
    assert {t: rows(migration_database, t) for t in before} == before
    assert counts(migration_database, AUTHORITY_TABLES) == {
        t: n + 1 for t, n in authority_before.items()
    }
    parent = client.get(f"/api/staff/v1/employers/{refs['employer']['id']}")
    assert parent.status_code == 200, parent.text
    assert parent.json()["version"] == 2
    if command_kind == "link":
        assert dependencies(migration_database, target) == {}
    else:
        assert dependencies(migration_database, target)["employer"] == reference(refs["employer"])


def test_finalization_holds_parent_until_commit_then_revision_preserves_original_outputs(
    client, migration_database
):
    refs = canonical(client, "business")
    target = draft_employer(client, "business")
    link(
        migration_database,
        target,
        1,
        reference(refs["employer"]),
        contact=reference(refs["contact"]),
        worksite=reference(refs["worksite"]),
        business_address=reference(refs["business_address"]),
    )
    body = review(client, target, 2)
    saved_reviews = rows(migration_database, "intake_review_payloads")
    saved_links = rows(migration_database, "intake_links")
    before = counts(migration_database, (*AUTHORITY_TABLES, *EMPLOYER_TABLES))
    finished, revised = commit_before_waiter(
        migration_database,
        operation(
            execute_new_intake_finalization, target, FinalizeIntakeRequest.model_validate(body)
        ),
        revision(refs, "household"),
    )
    result, replayed = finished["value"]
    assert not replayed
    assert revised["value"].result_record_version == 2
    assert revised["value"].employer.employer_type == "household"
    assert result["finalization"]["employer"] == {
        **reference(refs["employer"]),
        "disposition": "reused",
    }
    expected = dict(before)
    expected["staffing_requests"] += 1
    expected["command_receipts"] += 2
    expected["command_results"] += 3
    expected["audit_events"] += 3
    assert counts(migration_database, expected) == expected
    assert rows(migration_database, "intake_review_payloads") == saved_reviews
    assert rows(migration_database, "intake_links") == saved_links
    final = next(
        r for r in rows(migration_database, "intake_finalizations") if str(r["intake_id"]) == target
    )
    assert final["employer_version"] == 1 and final["employer_disposition"] == "reused"
    request = next(
        r
        for r in rows(migration_database, "staffing_requests")
        if r["staffing_request_id"] == final["staffing_request_id"]
    )
    assert request["request_type"] == "general_labor"
    assert str(request["employer_address_id"]) == refs["business_address"]["id"]
    intake = next(r for r in rows(migration_database, "intakes") if str(r["intake_id"]) == target)
    assert intake["lifecycle_status"] == "finalized" and intake["version"] == 4
    detail = client.get(f"/api/staff/v1/intakes/{target}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["dependency_stale"]
    assert detail.json()["resolved"]["employer_type"] == "household"
    assert detail.json()["finalization"] == result["finalization"]
    retry = client.post(
        f"/api/staff/v1/intakes/{target}/finalizations",
        json=body,
        headers={"Idempotency-Key": result["command_id"]},
    )
    assert retry.status_code == 200, retry.text
    assert retry.headers["Idempotency-Replayed"] == "true"
    assert retry.json()["finalization"] == result["finalization"]
    assert counts(migration_database, expected) == expected
