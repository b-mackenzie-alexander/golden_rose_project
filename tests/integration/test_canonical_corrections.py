"""Real command authority, immutable history and exact replay acceptance."""

from dataclasses import replace
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from golden_rose.application.correct_canonical_records import execute_correction
from golden_rose.application.intake_errors import IntakeError
from golden_rose.persistence.canonical_corrections import SPECS
from golden_rose.persistence.models import (
    canonical_correction_payloads,
    intake_finalizations,
    workers,
)
from tests.integration.test_intake_commands import Clock
from tests.integration.test_intake_finalization import FINALIZER, finalize, review
from tests.integration.test_intake_finalization import draft as draft

CORRECTOR = replace(
    FINALIZER,
    permissions=FINALIZER.permissions
    | frozenset(p for spec in SPECS.values() for p in spec.permissions),
)


def corrected(
    session, target, name="Fictional Corrected", *, key=None, version=1, principal=CORRECTOR
) -> tuple[dict[str, Any], bool]:
    return execute_correction(
        session=session,
        principal=principal,
        command_id=key or uuid4(),
        command_type="correct_worker",
        parent_id=target,
        target_id=target,
        request=SPECS["correct_worker"].model.model_validate(
            {"expected_version": version, "reason_text": "Fictional correction", "full_name": name}
        ),
        clock=Clock(),
    )


def test_finalized_intake_review_and_original_output_versions_never_change(session, draft):
    result, _ = finalize(session, draft, review(session, draft, 1))
    original = dict(session.execute(select(intake_finalizations)).mappings().one())
    worker = UUID(result["finalization"]["worker"]["id"])
    response, replay = corrected(session, worker)
    assert not replay
    assert response["result_record_version"] == 2
    assert session.scalar(select(workers.c.full_name)) == "Fictional Corrected"
    assert dict(session.execute(select(intake_finalizations)).mappings().one()) == original
    payload = session.execute(select(canonical_correction_payloads)).mappings().one()
    assert payload["before"] == {"full_name": "Fictional Finalization Worker"}
    assert payload["after"] == {"full_name": "Fictional Corrected"}


def test_unknown_commit_retry_replays_once_and_revocation_denies(session, draft):
    result, _ = finalize(session, draft, review(session, draft, 1))
    target = UUID(result["finalization"]["worker"]["id"])
    key = uuid4()
    first, _ = corrected(session, target, key=key)
    corrected(session, target, "Fictional Later", version=2)
    second, replay = corrected(session, target, key=key)
    assert replay and second["event_id"] == first["event_id"]
    assert second["result_record_version"] == 2
    assert second["target"]["current_version"] == 3
    revoked = replace(CORRECTOR, permissions=CORRECTOR.permissions - {"worker:correct"})
    with pytest.raises(IntakeError, match="forbidden"):
        corrected(session, target, key=key, principal=revoked)


def test_stale_and_changed_key_payload_cannot_overwrite(session, draft):
    result, _ = finalize(session, draft, review(session, draft, 1))
    target = UUID(result["finalization"]["worker"]["id"])
    key = uuid4()
    corrected(session, target, key=key)
    with pytest.raises(IntakeError, match="idempotency_conflict"):
        corrected(session, target, "Fictional Changed", key=key)
    with pytest.raises(IntakeError, match="version_conflict"):
        corrected(session, target, "Fictional Stale")


def test_direct_sql_rejects_unaudited_correction_and_identity_change(session, draft):
    finalize(session, draft, review(session, draft, 1))
    for sql in (
        "UPDATE workers SET full_name='Fictional Bypass',version=version+1",
        "UPDATE workers SET worker_id=gen_random_uuid(),version=version+1",
    ):
        with pytest.raises(IntegrityError):
            session.execute(text(sql))
            session.commit()
        session.rollback()


def test_correction_of_correction_requires_same_target_and_retains_both_snapshots(session, draft):
    result, _ = finalize(session, draft, review(session, draft, 1))
    target = UUID(result["finalization"]["worker"]["id"])
    first, _ = corrected(session, target)

    def request(event_id: Any) -> Any:
        return SPECS["correct_worker"].model.model_validate(
            {
                "expected_version": 2,
                "reason_text": "Fictional correction of correction",
                "corrects_event_id": str(event_id),
                "full_name": "Fictional corrected again",
            }
        )

    arguments: dict[str, Any] = {
        "session": session,
        "principal": CORRECTOR,
        "command_type": "correct_worker",
        "parent_id": target,
        "target_id": target,
        "clock": Clock(),
    }
    with pytest.raises(IntakeError, match="invalid_request"):
        execute_correction(**arguments, command_id=uuid4(), request=request(uuid4()))
    second, _ = execute_correction(
        **arguments, command_id=uuid4(), request=request(first["event_id"])
    )
    assert second["result_record_version"] == 3
    payloads = session.execute(select(canonical_correction_payloads)).mappings().all()
    assert len(payloads) == 2
    assert next(p for p in payloads if str(p["event_id"]) == second["event_id"])["before"] == {
        "full_name": "Fictional Corrected"
    }
    assert next(p for p in payloads if str(p["event_id"]) == first["event_id"])["before"] == {
        "full_name": "Fictional Finalization Worker"
    }
