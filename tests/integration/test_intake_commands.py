"""Real PostgreSQL transaction, retry and section-isolation acceptance tests."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from threading import Barrier
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_schemas import (
    CreateIntakeRequest,
    ReviseIntakeAddressRequest,
    ReviseIntakeRequest,
)
from golden_rose.application.intake_commands import execute_intake
from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.intakes import get_address, get_intake

PERMISSIONS = frozenset(
    {"intake:read", "intake:draft:create", "intake:draft:revise"}
    | {
        f"{section}:{action}"
        for section in ("worker_residence", "party_address", "worksite_address")
        for action in ("read", "write")
    }
)
PRINCIPAL = StaffPrincipal(UUID("22222222-2222-4222-8222-222222222222"), "test", PERMISSIONS)


class Clock:
    def now(self) -> datetime:
        return datetime(2026, 9, 14, tzinfo=UTC)


def create(
    session: Session,
    *,
    command_id: UUID | None = None,
    principal: StaffPrincipal = PRINCIPAL,
    content: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], bool]:
    return execute_intake(
        session=session,
        principal=principal,
        command_id=command_id or uuid4(),
        request=CreateIntakeRequest.model_validate(
            {
                "kind": "worker",
                "content": content if content is not None else {"phone": "+12025550123"},
            }
        ),
        clock=Clock(),
    )


def counts(session: Session) -> tuple[int, ...]:
    return tuple(
        session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
        for table in ("intakes", "command_receipts", "command_results", "audit_events")
    )


def test_create_commits_exact_authority_and_survives_lost_response(clean_tables, engine):
    key = uuid4()
    with Session(engine) as first:
        created, replayed = create(first, command_id=key)
        assert not replayed
    # The first caller discards its response and closes its session before retry.
    with Session(engine) as second:
        recovered, replayed = create(second, command_id=key)
        assert replayed and recovered == created
        assert counts(second) == (1, 1, 1, 1)
        receipt = second.execute(text("SELECT * FROM command_receipts")).mappings().one()
        result = second.execute(text("SELECT * FROM command_results")).mappings().one()
        audit = second.execute(text("SELECT * FROM audit_events")).mappings().one()
        assert receipt["command_id"] == result["command_id"] == audit["command_id"] == key
        assert receipt["result_entity_id"] == result["entity_id"] == audit["entity_id"]
        assert receipt["result_record_version"] == result["result_version"] == 1
        assert audit["prior_record_version"] == 0 and audit["new_record_version"] == 1
        assert audit["changed_fields"] == {"field_names": ["phone"], "approved_values": {}}


def test_failure_after_candidate_write_rolls_back_every_authority(clean_tables, engine):
    def fail_audit(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO audit_events"):
            raise OperationalError(statement, {}, RuntimeError("fictional storage failure"))

    event.listen(engine, "before_cursor_execute", fail_audit)
    try:
        with Session(engine) as session, pytest.raises(IntakeError) as error:
            create(session)
        assert error.value.status == 503
    finally:
        event.remove(engine, "before_cursor_execute", fail_audit)
    with Session(engine) as check:
        assert counts(check) == (0, 0, 0, 0)


def test_two_sessions_same_key_commit_only_once(clean_tables, engine):
    gate, key = Barrier(2), uuid4()

    def attempt():
        with Session(engine) as session:
            gate.wait(timeout=5)
            return create(session, command_id=key)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(attempt) for _ in range(2)]
        outcomes = [future.result(timeout=15) for future in futures]
    assert sorted(replayed for _, replayed in outcomes) == [False, True]
    assert outcomes[0][0] == outcomes[1][0]
    with Session(engine) as check:
        assert counts(check) == (1, 1, 1, 1)


def test_retry_reauthorizes_actor_payload_and_revoked_permission(clean_tables, session):
    key = uuid4()
    create(session, command_id=key)
    for principal, content, expected in [
        (replace(PRINCIPAL, actor_id=uuid4()), None, "idempotency_conflict"),
        (PRINCIPAL, {"phone": "+12025550124"}, "idempotency_conflict"),
        (replace(PRINCIPAL, permissions=frozenset({"intake:read"})), None, "forbidden"),
    ]:
        with pytest.raises(IntakeError) as error:
            create(session, command_id=key, principal=principal, content=content)
        assert error.value.code == expected
    assert counts(session) == (1, 1, 1, 1)


def test_stale_and_no_change_do_not_create_receipts(clean_tables, session):
    created, _ = create(session)
    target = UUID(created["current"]["summary"]["intake_id"])
    for version, content, expected in [
        (2, {"full_name": "Fictional Worker"}, "version_conflict"),
        (1, {"phone": "+12025550123"}, "no_change"),
    ]:
        with pytest.raises(IntakeError) as error:
            execute_intake(
                session=session,
                principal=PRINCIPAL,
                command_id=uuid4(),
                request=ReviseIntakeRequest.model_validate(
                    {"expected_version": version, "content": content}
                ),
                clock=Clock(),
                intake_id=target,
            )
        assert error.value.code == expected
    assert counts(session) == (1, 1, 1, 1)


def test_content_then_unknown_address_then_later_content_retry_preserves_values(
    clean_tables, engine
):
    with Session(engine) as session:
        created, _ = create(session)
        target = UUID(created["current"]["summary"]["intake_id"])
        execute_intake(
            session=session,
            principal=PRINCIPAL,
            command_id=uuid4(),
            request=ReviseIntakeRequest.model_validate(
                {
                    "expected_version": 1,
                    "content": {"phone": "+12025550123", "full_name": "Fictional Worker"},
                }
            ),
            clock=Clock(),
            intake_id=target,
        )
        address_key = uuid4()
        address = ReviseIntakeAddressRequest.model_validate(
            {"expected_version": 2, "address": {"line1": "17 Fictional Lane", "country": "US"}}
        )
        execute_intake(
            session=session,
            principal=PRINCIPAL,
            command_id=address_key,
            request=address,
            clock=Clock(),
            intake_id=target,
            section="worker_residence",
        )
        # Response was lost; another successful content save advances the record.
        execute_intake(
            session=session,
            principal=PRINCIPAL,
            command_id=uuid4(),
            request=ReviseIntakeRequest.model_validate(
                {
                    "expected_version": 3,
                    "content": {"phone": "+12025550123", "full_name": "Fictional Revised"},
                }
            ),
            clock=Clock(),
            intake_id=target,
        )
    with Session(engine) as recovered:
        result, replayed = execute_intake(
            session=recovered,
            principal=PRINCIPAL,
            command_id=address_key,
            request=address,
            clock=Clock(),
            intake_id=target,
            section="worker_residence",
        )
        assert replayed and result["result_record_version"] == 3
        assert result["current"]["summary"]["version"] == 4
        assert result["current"]["candidate"]["full_name"] == "Fictional Revised"
        assert "17 Fictional Lane" not in str(result)
        assert get_address(recovered, target, "worker_residence") == {
            "line1": "17 Fictional Lane",
            "country": "US",
        }
        assert get_intake(recovered, target)["content_version"] == 4
        assert counts(recovered) == (1, 4, 4, 4)


def test_runtime_role_can_save_resume_and_cannot_delete(clean_tables, engine):
    # Bind Session to this one connection: SET ROLE must not escape into the pool.
    with engine.connect() as connection:
        connection.execute(text("SET ROLE golden_rose_runtime"))
        connection.commit()
        try:
            with Session(bind=connection) as session:
                created, _ = create(session)
                target = UUID(created["current"]["summary"]["intake_id"])
                response, _ = execute_intake(
                    session=session,
                    principal=PRINCIPAL,
                    command_id=uuid4(),
                    clock=Clock(),
                    intake_id=target,
                    request=ReviseIntakeRequest.model_validate(
                        {"expected_version": 1, "content": {"phone": "+12025550124"}}
                    ),
                )
                assert response["current"]["summary"]["version"] == 2
                response, _ = execute_intake(
                    session=session,
                    principal=PRINCIPAL,
                    command_id=uuid4(),
                    clock=Clock(),
                    intake_id=target,
                    section="worker_residence",
                    request=ReviseIntakeAddressRequest.model_validate(
                        {"expected_version": 2, "address": {"line1": "Fictional Runtime Lane"}}
                    ),
                )
                assert response["current"]["summary"]["version"] == 3
                assert get_address(session, target, "worker_residence") == {
                    "line1": "Fictional Runtime Lane"
                }
                session.rollback()
                from sqlalchemy.exc import DBAPIError

                with pytest.raises(DBAPIError):
                    session.execute(text("DELETE FROM intakes WHERE intake_id=:id"), {"id": target})
                session.rollback()
                assert get_intake(session, target)["version"] == 3
        finally:
            connection.rollback()
            connection.execute(text("RESET ROLE"))
            connection.commit()
