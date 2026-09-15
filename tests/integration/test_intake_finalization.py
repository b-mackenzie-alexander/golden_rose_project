"""Real PostgreSQL review preconditions and new-worker finalization acceptance."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event, func, select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_finalization_schemas import FinalizeIntakeRequest
from golden_rose.api.staff.intake_review_schemas import FollowUpIntakeRequest, ReviewIntakeRequest
from golden_rose.api.staff.intake_schemas import ReviseIntakeRequest
from golden_rose.application.finalize_intake import require_finalization_review
from golden_rose.application.intake_commands import execute_intake
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.intake_workflow_common import write_result_authority
from golden_rose.application.review_intake import execute_review
from golden_rose.auth.staff_directory import StaffDirectory, StaffDirectoryEntry
from golden_rose.persistence.intakes import get_intake
from golden_rose.persistence.models import audit_events, command_receipts, intakes
from tests.integration.test_intake_commands import PRINCIPAL, Clock, create

FINALIZER = replace(
    PRINCIPAL,
    permissions=PRINCIPAL.permissions | {"intake:review", "intake:follow_up", "intake:finalize"},
)
DIRECTORY = StaffDirectory(
    (StaffDirectoryEntry(FINALIZER.actor_id, "Fictional Finalizer", True, FINALIZER.permissions),)
)


@pytest.fixture
def draft(clean_tables, session) -> UUID:
    result, _ = create(
        session,
        principal=FINALIZER,
        content={
            "full_name": "Fictional Finalization Worker",
            "phone": "+12025550123",
            "interests": {"other_description": "Fictional gardening"},
            "availability": {"mode": "flexible"},
            "residential_address": {
                "line1": "10 Fictional Road",
                "locality": "Fictional City",
                "country": "US",
                "region": "NY",
                "postal_code": "10001",
            },
        },
    )
    return UUID(result["current"]["summary"]["intake_id"])


def review(session, intake_id, expected_version, *, follow_up=False) -> UUID:
    data = {"expected_version": expected_version, "outcome": "intake_reviewed"}
    if follow_up:
        data.update(
            outcome="needs_follow_up",
            reason_code="clarification",
            reason_text="Fictional clarification",
            owner_staff_id=str(FINALIZER.actor_id),
            next_follow_up_at="2026-09-15T12:00:00Z",
            time_zone="UTC",
        )
    result, _ = execute_review(
        session=session,
        principal=FINALIZER,
        command_id=uuid4(),
        request=ReviewIntakeRequest.model_validate(data),
        clock=Clock(),
        directory=DIRECTORY,
        intake_id=intake_id,
    )
    return UUID(str(result["current"]["latest_review"]["review_id"]))


def check_review(session, intake_id, review_id, version, *, principal=FINALIZER) -> None:
    row = get_intake(session, intake_id, lock=True)
    require_finalization_review(
        session=session,
        principal=principal,
        row=row,
        request=FinalizeIntakeRequest(expected_version=version, review_id=review_id),
        dependency_refs={},
    )


def test_finalization_precondition_uses_latest_persisted_disposition(session, draft):
    first = review(session, draft, 1)
    second = review(session, draft, 2)
    with pytest.raises(IntakeError, match="review_required"):
        check_review(session, draft, first, 3)
    check_review(session, draft, second, 3)
    third = review(session, draft, 3, follow_up=True)
    for review_id in (second, third):
        with pytest.raises(IntakeError, match="review_required"):
            check_review(session, draft, review_id, 4)
    assert session.scalar(select(func.count()).select_from(audit_events)) == 4
    assert session.scalar(select(func.count()).select_from(command_receipts)) == 4
    assert session.scalar(select(intakes.c.lifecycle_status)) == "draft"


def test_finalization_precondition_rejects_changed_content(session, draft):
    reviewed = review(session, draft, 1)
    content = {**get_intake(session, draft)["content"], "full_name": "Fictional Revised Worker"}
    execute_intake(
        session=session,
        principal=FINALIZER,
        command_id=uuid4(),
        request=ReviseIntakeRequest.model_validate({"expected_version": 2, "content": content}),
        clock=Clock(),
        intake_id=draft,
    )
    with pytest.raises(IntakeError, match="version_conflict"):
        check_review(session, draft, reviewed, 2)
    with pytest.raises(IntakeError, match="review_required"):
        check_review(session, draft, reviewed, 3)


def test_finalization_precondition_ignores_newer_review_on_another_intake(session, draft):
    reviewed = review(session, draft, 1)
    other_result, _ = create(session, principal=FINALIZER)
    other = UUID(other_result["current"]["summary"]["intake_id"])
    for version in range(1, 4):
        review(session, other, version, follow_up=True)
    check_review(session, draft, reviewed, 2)
    assert get_intake(session, other)["version"] == 4


def test_finalization_precondition_accepts_bookkeeping_after_review(session, draft, engine):
    review(session, draft, 1, follow_up=True)
    reviewed = review(session, draft, 2)
    execute_review(
        session=session,
        principal=FINALIZER,
        command_id=uuid4(),
        request=FollowUpIntakeRequest.model_validate(
            {
                "expected_version": 3,
                "action": "reschedule",
                "reason_text": "Fictional reschedule",
                "owner_staff_id": str(FINALIZER.actor_id),
                "next_follow_up_at": "2026-09-16T12:00:00Z",
                "time_zone": "UTC",
            }
        ),
        clock=Clock(),
        directory=DIRECTORY,
        intake_id=draft,
    )
    with Session(engine) as later:
        check_review(later, draft, reviewed, 4)
        assert get_intake(later, draft)["content_version"] == 1
        assert later.scalar(select(func.count()).select_from(command_receipts)) == 4


@pytest.mark.parametrize("permission", ["intake:finalize", "worker_residence:read"])
def test_finalization_precondition_rejects_revocation(session, draft, permission):
    reviewed = review(session, draft, 1)
    revoked = replace(FINALIZER, permissions=FINALIZER.permissions - {permission})
    with pytest.raises(IntakeError) as caught:
        check_review(session, draft, reviewed, 2, principal=revoked)
    assert caught.value.status == 403
    assert get_intake(session, draft)["version"] == 2
    assert session.scalar(select(func.count()).select_from(command_receipts)) == 2


def finalize(
    session, intake_id, review_id, *, key=None, principal=FINALIZER, version=2
) -> tuple[dict[str, Any], bool]:
    from golden_rose.application.finalize_intake import execute_new_intake_finalization

    return execute_new_intake_finalization(
        session=session,
        principal=principal,
        intake_id=intake_id,
        command_id=key or uuid4(),
        request=FinalizeIntakeRequest(expected_version=version, review_id=review_id),
        clock=Clock(),
    )


def output_counts(session) -> tuple[int, ...]:
    return tuple(
        session.scalar(text(f"SELECT count(*) FROM {table}"))
        for table in (
            "workers",
            "worker_contacts",
            "worker_residences",
            "worker_preferences",
            "intake_finalizations",
        )
    )


def test_new_worker_finalization_is_atomic_and_duplicate_safe(session, draft, engine):
    reviewed = review(session, draft, 1)
    key = uuid4()
    original, replayed = finalize(session, draft, reviewed, key=key)
    assert not replayed
    assert original["result_record_version"] == 3
    outputs = original["finalization"]
    assert outputs["kind"] == "worker"
    for name in ("worker", "contact", "residence", "preferences"):
        assert outputs[name]["disposition"] == "created"
        assert outputs[name]["version"] == 1
    with Session(engine) as later:
        recovered, replayed = finalize(later, draft, reviewed, key=key)
        assert replayed
        assert recovered == original
        assert output_counts(later) == (1, 1, 1, 1, 1)
        assert (
            later.scalar(
                text("SELECT count(*) FROM command_results WHERE command_id=:key"), {"key": key}
            )
            == 5
        )
        assert (
            later.scalar(
                text("SELECT count(*) FROM audit_events WHERE command_id=:key"), {"key": key}
            )
            == 5
        )
        assert (
            later.scalar(text("SELECT full_name FROM workers")) == "Fictional Finalization Worker"
        )
        assert later.scalar(text("SELECT phone FROM worker_contacts")) == "+12025550123"
        assert later.scalar(text("SELECT line1 FROM worker_residences")) == "10 Fictional Road"
        assert later.scalar(text("SELECT self_reported FROM worker_preferences")) is True
        assert get_intake(later, draft)["content_version"] == 1


def test_finalize_rollback_leaves_no_partial_canonical_group(session, draft, engine):
    reviewed = review(session, draft, 1)

    def fail_finalization(conn, cursor, statement, parameters, context, executemany) -> None:
        if statement.startswith("INSERT INTO intake_finalizations"):
            raise OperationalError(statement, {}, RuntimeError("fictional failure"))

    event.listen(engine, "before_cursor_execute", fail_finalization)
    try:
        with pytest.raises(IntakeError) as caught:
            finalize(session, draft, reviewed)
        assert caught.value.status == 503
    finally:
        event.remove(engine, "before_cursor_execute", fail_finalization)
    with Session(engine) as later:
        assert output_counts(later) == (0, 0, 0, 0, 0)
        assert get_intake(later, draft)["version"] == 2
        assert later.scalar(select(func.count()).select_from(command_receipts)) == 2


@pytest.mark.parametrize("permission", ["intake:finalize", "worker_residence:write"])
def test_finalization_replay_rechecks_current_permission(session, draft, permission):
    reviewed = review(session, draft, 1)
    key = uuid4()
    finalize(session, draft, reviewed, key=key)
    revoked = replace(FINALIZER, permissions=FINALIZER.permissions - {permission})
    with pytest.raises(IntakeError) as caught:
        finalize(session, draft, reviewed, key=key, principal=revoked)
    assert caught.value.status == 403
    assert output_counts(session) == (1, 1, 1, 1, 1)


def test_finalization_new_key_cannot_create_a_second_group(session, draft):
    reviewed = review(session, draft, 1)
    key = uuid4()
    finalize(session, draft, reviewed, key=key)
    with pytest.raises(IntakeError, match="already_finalized"):
        finalize(session, draft, reviewed)
    with pytest.raises(IntakeError, match="idempotency_conflict"):
        finalize(session, draft, uuid4(), key=key)
    assert output_counts(session) == (1, 1, 1, 1, 1)


@pytest.mark.parametrize("same_key", [False, True])
def test_one_intake_finalize_race_has_one_output_set(session, draft, engine, same_key):
    reviewed = review(session, draft, 1)
    gate, key = Barrier(2), uuid4()

    def attempt() -> Any:
        with Session(engine) as connection:
            gate.wait(timeout=5)
            try:
                _, replayed = finalize(
                    connection, draft, reviewed, key=key if same_key else uuid4()
                )
                return "replayed" if replayed else "created"
            except IntakeError as exc:
                return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = [pool.submit(attempt) for _ in range(2)]
        results = sorted(item.result(timeout=15) for item in outcomes)
    assert results == (["created", "replayed"] if same_key else ["already_finalized", "created"])
    with Session(engine) as later:
        assert output_counts(later) == (1, 1, 1, 1, 1)


@pytest.mark.parametrize("fault", ["missing", "wrong_actor", "extra"])
def test_commit_rejects_missing_extra_or_wrong_actor_results(session, draft, monkeypatch, fault):
    from golden_rose.application import finalize_intake

    reviewed = review(session, draft, 1)
    original = write_result_authority

    def corrupted(connection, **values) -> Any:
        if values["entity_type"] == "worker_contact":
            if fault == "missing":
                return
            if fault == "wrong_actor":
                values["principal"] = replace(values["principal"], actor_id=uuid4())
            if fault == "extra":
                original(connection, **{**values, "entity_id": uuid4(), "event_id": uuid4()})
        return original(connection, **values)

    monkeypatch.setattr(finalize_intake, "write_result_authority", corrupted)
    with pytest.raises(IntakeError) as caught:
        finalize(session, draft, reviewed)
    assert caught.value.status == 503
    assert output_counts(session) == (0, 0, 0, 0, 0)
    assert get_intake(session, draft)["version"] == 2


def test_finalized_intake_reopens_and_history_contains_no_canonical_fields(session, draft):
    from golden_rose.api.staff.intake_review_schemas import IntakeHistoryPage, PageRequest
    from golden_rose.api.staff.intake_schemas import IntakeCommandResponse
    from golden_rose.application.intake_history import query_history

    reviewed = review(session, draft, 1)
    result, _ = finalize(session, draft, reviewed)
    validated = IntakeCommandResponse.model_validate(result)
    assert validated.current.summary.lifecycle == "finalized"
    assert validated.current.finalization == validated.finalization
    history = query_history(
        session=session,
        principal=FINALIZER,
        directory=DIRECTORY,
        intake_id=draft,
        request=PageRequest(),
    )
    assert IntakeHistoryPage.model_validate(history).items[0].event_type == "intake.finalized"
    assert "10 Fictional Road" not in str(history)


@pytest.mark.parametrize("retired", [False, True])
def test_finalization_preserves_catalog_refs_and_rejects_retirement(session, draft, retired):
    from golden_rose.api.staff.intake_review_schemas import (
        CreateWorkInterestRequest,
        ReviseWorkInterestRequest,
    )
    from golden_rose.application.work_interests import execute_work_interest

    principal = replace(
        FINALIZER,
        permissions=FINALIZER.permissions
        | {
            "work_interest:read",
            "work_interest:manage",
        },
    )
    catalog, _ = execute_work_interest(
        session=session,
        principal=principal,
        command_id=uuid4(),
        request=CreateWorkInterestRequest(
            code="fictional_garden", label_en="Fictional gardening", label_es="Jardineria ficticia"
        ),
        clock=Clock(),
    )
    interest_id = UUID(catalog["current"]["interest_id"])
    content = {
        **get_intake(session, draft)["content"],
        "interests": {"selections": [{"interest_id": str(interest_id), "catalog_version": 1}]},
    }
    execute_intake(
        session=session,
        principal=principal,
        command_id=uuid4(),
        intake_id=draft,
        request=ReviseIntakeRequest.model_validate({"expected_version": 1, "content": content}),
        clock=Clock(),
    )
    reviewed, _ = execute_review(
        session=session,
        principal=principal,
        command_id=uuid4(),
        request=ReviewIntakeRequest(expected_version=2, outcome="intake_reviewed"),
        clock=Clock(),
        directory=DIRECTORY,
        intake_id=draft,
    )
    review_id = UUID(str(reviewed["current"]["latest_review"]["review_id"]))
    if retired:
        execute_work_interest(
            session=session,
            principal=principal,
            command_id=uuid4(),
            interest_id=interest_id,
            request=ReviseWorkInterestRequest(
                expected_version=1,
                label_en="Fictional gardening",
                label_es="Jardineria ficticia",
                active=False,
            ),
            clock=Clock(),
        )
        with pytest.raises(IntakeError) as caught:
            finalize(session, draft, review_id, principal=principal, version=3)
        assert caught.value.code == "incomplete"
        assert output_counts(session) == (0, 0, 0, 0, 0)
    else:
        result, _ = finalize(session, draft, review_id, principal=principal, version=3)
        selection = session.execute(
            text("SELECT interest_id,catalog_version FROM worker_interest_selections")
        ).one()
        assert selection == (interest_id, 1)
        assert result["result_record_version"] == 4
