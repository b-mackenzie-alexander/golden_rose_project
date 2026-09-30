from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import NoResultFound, SQLAlchemyError

from golden_rose.api.staff.employer_output_schemas import (
    CreateShiftNeedRequest,
    QueryShiftNeedsRequest,
    SubmitForReviewRequest,
)
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.shift_needs import (
    create_shift_need,
    query_shift_needs,
    read_shift_need,
    submit_shift_need_for_review,
    submit_staffing_request_for_review,
)
from golden_rose.auth.principal import StaffPrincipal

ACTOR_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYER_ID = UUID("22222222-2222-4222-8222-222222222222")
REQUEST_ID = UUID("33333333-3333-4333-8333-333333333333")
SHIFT_ID = UUID("44444444-4444-4444-8444-444444444444")
COMMAND_ID = UUID("55555555-5555-4555-8555-555555555555")
NOW = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)


class FakeResult:
    def __init__(self, value: Any = None, *, missing: bool = False) -> None:
        self.value = value
        self.missing = missing

    def mappings(self) -> "FakeResult":
        return self

    def one_or_none(self) -> Any:
        return self.value

    def one(self) -> Any:
        if self.missing:
            raise NoResultFound
        return self.value

    def all(self) -> Any:
        return self.value


class FakeSession:
    def __init__(self, results: list[FakeResult | Exception]) -> None:
        self.results = list(results)
        self.commits = 0
        self.rollbacks = 0
        self.executed: list[Any] = []

    def execute(self, statement: Any) -> FakeResult:
        self.executed.append(statement)
        if not self.results:
            return FakeResult()
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def principal(*permissions: str) -> StaffPrincipal:
    return StaffPrincipal(ACTOR_ID, "operations_staff", frozenset(permissions))


def body(**changes: Any) -> CreateShiftNeedRequest:
    values = {
        "expected_request_version": 2,
        "role_title": "Home aide",
        "worker_count": 2,
        "starts_at": "2026-10-01T13:00:00Z",
        "ends_at": "2026-10-01T17:00:00Z",
        "time_zone": "America/New_York",
        "reason_text": "Employer supplied a concrete shift",
    }
    values.update(changes)
    return CreateShiftNeedRequest.model_validate(values)


def review_body(**changes: Any) -> SubmitForReviewRequest:
    values = {"expected_version": 1, "reason_text": "Staff submitted for review"}
    values.update(changes)
    return SubmitForReviewRequest.model_validate(values)


def shift_detail(**changes: Any) -> dict[str, Any]:
    values = {
        "shift_need_id": SHIFT_ID,
        "employer_id": EMPLOYER_ID,
        "staffing_request_id": REQUEST_ID,
        "request_version_at_creation": 2,
        "shift_status": "draft",
        "role_title": "Home aide",
        "worker_count": 1,
        "starts_at": datetime(2026, 10, 1, 13, 0, tzinfo=UTC),
        "ends_at": datetime(2026, 10, 1, 17, 0, tzinfo=UTC),
        "time_zone": "America/New_York",
        "notes": None,
        "version": 1,
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(changes)
    return values


def request_detail(**changes: Any) -> dict[str, Any]:
    values = {
        "staffing_request_id": REQUEST_ID,
        "employer_id": EMPLOYER_ID,
        "version": 3,
        "employer_contact_id": UUID("66666666-6666-4666-8666-666666666666"),
        "worksite_id": UUID("77777777-7777-4777-8777-777777777777"),
        "employer_address_id": None,
        "request_type": "household",
        "request_status": "pending_review",
        "source_channel": "staff_entry",
        "role_title": "Home aide",
        "duties_summary": "Help at home",
        "worker_count": 1,
        "schedule": {"mode": "to_be_discussed"},
        "offer": {"minimum": "18.00", "currency": "USD", "basis": "hourly", "per_worker": True},
        "created_at": NOW,
        "received_at": NOW,
        "updated_at": NOW,
    }
    values.update(changes)
    return values


def all_permissions() -> StaffPrincipal:
    return principal(
        "employer:read",
        "staffing_request:read",
        "shift_need:create",
        "shift_need:read",
        "shift_need:submit_review",
        "staffing_request:submit_review",
    )


def test_shift_need_schema_requires_ordered_timezone_aware_datetimes():
    with pytest.raises(ValidationError):
        CreateShiftNeedRequest.model_validate(
            {
                "expected_request_version": 1,
                "role_title": "Home aide",
                "worker_count": 1,
                "starts_at": "not-a-date",
                "ends_at": "2026-10-01T17:00:00Z",
                "time_zone": "America/New_York",
                "reason_text": "Concrete schedule supplied",
            }
        )


def test_create_shift_need_records_draft_child_and_event():
    session = FakeSession(
        [
            FakeResult(None),
            FakeResult({"version": 2, "role_title": "Home aide", "worker_count": 3}),
            FakeResult(),
            FakeResult(),
        ]
    )

    result = create_shift_need(
        session=session,  # type: ignore[arg-type]
        principal=all_permissions(),
        employer_id=EMPLOYER_ID,
        request_id=REQUEST_ID,
        command_id=COMMAND_ID,
        body=body(),
        now=NOW,
    )

    assert result.replayed is False
    assert result.payload["command_id"] == COMMAND_ID
    assert result.payload["result_record_version"] == 1
    assert result.payload["event_type"] == "shift_need.created"
    assert session.commits == 1
    assert session.rollbacks == 0
    assert len(session.executed) == 4


def test_create_shift_need_requires_explicit_shift_permissions():
    with pytest.raises(IntakeError) as error:
        create_shift_need(
            session=FakeSession([]),  # type: ignore[arg-type]
            principal=principal("employer:read", "staffing_request:read"),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            command_id=COMMAND_ID,
            body=body(),
            now=NOW,
        )
    assert error.value.status == 403


def test_query_shift_needs_requires_explicit_read_permissions():
    with pytest.raises(IntakeError) as error:
        query_shift_needs(
            session=FakeSession([]),  # type: ignore[arg-type]
            principal=principal("employer:read", "staffing_request:read"),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            request=QueryShiftNeedsRequest(),
        )
    assert error.value.status == 403


def test_query_shift_needs_returns_draft_children():
    detail = shift_detail(notes="Prefers morning coverage")
    session = FakeSession([FakeResult({"staffing_request_id": REQUEST_ID}), FakeResult([detail])])

    result = query_shift_needs(
        session=session,  # type: ignore[arg-type]
        principal=all_permissions(),
        employer_id=EMPLOYER_ID,
        request_id=REQUEST_ID,
        request=QueryShiftNeedsRequest(page_size=10),
    )

    assert result == {"items": [detail]}
    assert len(session.executed) == 2
    assert session.rollbacks == 0


def test_query_shift_needs_reports_missing_parent_request():
    with pytest.raises(IntakeError) as error:
        query_shift_needs(
            session=FakeSession([FakeResult(None)]),  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            request=QueryShiftNeedsRequest(),
        )
    assert error.value.status == 404


def test_query_shift_needs_rolls_back_persistence_errors():
    session = FakeSession([SQLAlchemyError("database unavailable")])

    with pytest.raises(IntakeError) as error:
        query_shift_needs(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            request=QueryShiftNeedsRequest(),
        )

    assert error.value.status == 503
    assert session.rollbacks == 1


def test_read_shift_need_returns_exact_draft_detail():
    detail = shift_detail()

    result = read_shift_need(
        session=FakeSession([FakeResult(detail)]),  # type: ignore[arg-type]
        principal=all_permissions(),
        employer_id=EMPLOYER_ID,
        request_id=REQUEST_ID,
        shift_need_id=SHIFT_ID,
    )

    assert result == detail


def test_read_shift_need_reports_missing_child():
    with pytest.raises(IntakeError) as error:
        read_shift_need(
            session=FakeSession([FakeResult(None)]),  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            shift_need_id=SHIFT_ID,
        )
    assert error.value.status == 404


def test_read_shift_need_rolls_back_persistence_errors():
    session = FakeSession([SQLAlchemyError("database unavailable")])

    with pytest.raises(IntakeError) as error:
        read_shift_need(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            shift_need_id=SHIFT_ID,
        )

    assert error.value.status == 503
    assert session.rollbacks == 1


def test_create_shift_need_rejects_naive_datetimes():
    invalid = CreateShiftNeedRequest.model_construct(
        expected_request_version=2,
        role_title="Home aide",
        worker_count=1,
        starts_at=datetime(2026, 10, 1, 13, 0),
        ends_at=datetime(2026, 10, 1, 17, 0, tzinfo=UTC),
        time_zone="America/New_York",
        reason_text="Concrete schedule supplied",
        notes=None,
    )

    with pytest.raises(IntakeError) as error:
        create_shift_need(
            session=FakeSession([]),  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            command_id=COMMAND_ID,
            body=invalid,
            now=NOW,
        )
    assert error.value.status == 422


def test_create_shift_need_rejects_unordered_times():
    with pytest.raises(IntakeError) as error:
        create_shift_need(
            session=FakeSession([]),  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            command_id=COMMAND_ID,
            body=body(starts_at="2026-10-01T17:00:00Z", ends_at="2026-10-01T13:00:00Z"),
            now=NOW,
        )
    assert error.value.status == 422


def test_create_shift_need_rejects_unknown_time_zone():
    with pytest.raises(IntakeError) as error:
        create_shift_need(
            session=FakeSession([]),  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            command_id=COMMAND_ID,
            body=body(time_zone="Atlantis/Golden_Rose"),
            now=NOW,
        )
    assert error.value.status == 422


def test_create_shift_need_rejects_command_reuse_for_another_request():
    session = FakeSession(
        [
            FakeResult(
                {
                    "command_id": COMMAND_ID,
                    "shift_need_id": SHIFT_ID,
                    "employer_id": EMPLOYER_ID,
                    "staffing_request_id": UUID("99999999-9999-4999-8999-999999999999"),
                    "actor_id": ACTOR_ID,
                    "event_type": "shift_need.created",
                    "new_version": 1,
                }
            )
        ]
    )

    with pytest.raises(IntakeError) as error:
        create_shift_need(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            command_id=COMMAND_ID,
            body=body(),
            now=NOW,
        )

    assert error.value.status == 409
    assert session.rollbacks == 1


def test_create_shift_need_reports_missing_replayed_detail():
    session = FakeSession(
        [
            FakeResult(
                {
                    "command_id": COMMAND_ID,
                    "shift_need_id": SHIFT_ID,
                    "employer_id": EMPLOYER_ID,
                    "staffing_request_id": REQUEST_ID,
                    "actor_id": ACTOR_ID,
                    "event_type": "shift_need.created",
                    "new_version": 1,
                }
            ),
            FakeResult(None),
        ]
    )

    with pytest.raises(IntakeError) as error:
        create_shift_need(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            command_id=COMMAND_ID,
            body=body(),
            now=NOW,
        )

    assert error.value.status == 404
    assert session.rollbacks == 1


def test_create_shift_need_reports_missing_parent_request():
    session = FakeSession([FakeResult(None), FakeResult(missing=True)])

    with pytest.raises(IntakeError) as error:
        create_shift_need(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            command_id=COMMAND_ID,
            body=body(),
            now=NOW,
        )

    assert error.value.status == 404
    assert session.rollbacks == 1


def test_create_shift_need_rejects_more_workers_than_parent_request():
    session = FakeSession(
        [
            FakeResult(None),
            FakeResult({"version": 2, "role_title": "Home aide", "worker_count": 1}),
        ]
    )

    with pytest.raises(IntakeError) as error:
        create_shift_need(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            command_id=COMMAND_ID,
            body=body(worker_count=2),
            now=NOW,
        )

    assert error.value.status == 422
    assert session.rollbacks == 1


def test_create_shift_need_rolls_back_persistence_errors():
    session = FakeSession([SQLAlchemyError("database unavailable")])

    with pytest.raises(IntakeError) as error:
        create_shift_need(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            command_id=COMMAND_ID,
            body=body(),
            now=NOW,
        )

    assert error.value.status == 503
    assert session.rollbacks == 1


def test_create_shift_need_rejects_stale_parent_version_and_rolls_back():
    session = FakeSession(
        [
            FakeResult(None),
            FakeResult({"version": 3, "role_title": "Home aide", "worker_count": 3}),
        ]
    )
    with pytest.raises(IntakeError) as error:
        create_shift_need(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            command_id=COMMAND_ID,
            body=body(expected_request_version=2),
            now=NOW,
        )
    assert error.value.status == 412
    assert session.rollbacks == 1
    assert session.commits == 0


def test_create_shift_need_replays_matching_command_without_new_write():
    existing = {
        "command_id": COMMAND_ID,
        "shift_need_id": SHIFT_ID,
        "employer_id": EMPLOYER_ID,
        "staffing_request_id": REQUEST_ID,
        "actor_id": ACTOR_ID,
        "event_type": "shift_need.created",
        "new_version": 1,
    }
    detail = shift_detail()
    session = FakeSession([FakeResult(existing), FakeResult(detail)])

    result = create_shift_need(
        session=session,  # type: ignore[arg-type]
        principal=all_permissions(),
        employer_id=EMPLOYER_ID,
        request_id=REQUEST_ID,
        command_id=COMMAND_ID,
        body=body(),
        now=NOW,
    )

    assert result.replayed is True
    assert result.payload["current"] == detail
    assert session.commits == 0
    assert len(session.executed) == 2


def test_submit_shift_need_for_review_records_transition_event():
    detail = shift_detail(shift_status="pending_review", version=2, updated_at=NOW)
    session = FakeSession(
        [
            FakeResult(None),
            FakeResult(
                {
                    "shift_status": "draft",
                    "version": 1,
                    "starts_at": datetime(2026, 10, 1, 13, 0, tzinfo=UTC),
                    "ends_at": datetime(2026, 10, 1, 17, 0, tzinfo=UTC),
                    "time_zone": "America/New_York",
                    "request_status": "draft",
                    "request_version": 2,
                }
            ),
            FakeResult(),
            FakeResult(),
            FakeResult(detail),
        ]
    )

    result = submit_shift_need_for_review(
        session=session,  # type: ignore[arg-type]
        principal=all_permissions(),
        employer_id=EMPLOYER_ID,
        request_id=REQUEST_ID,
        shift_need_id=SHIFT_ID,
        command_id=COMMAND_ID,
        body=review_body(),
        now=NOW,
    )

    assert result.replayed is False
    assert result.payload["event_type"] == "shift_need.submitted_for_review"
    assert result.payload["result_record_version"] == 2
    assert result.payload["current"] == detail
    assert session.commits == 1
    assert len(session.executed) == 5


def test_submit_shift_need_for_review_requires_explicit_permission():
    with pytest.raises(IntakeError) as error:
        submit_shift_need_for_review(
            session=FakeSession([]),  # type: ignore[arg-type]
            principal=principal("employer:read", "staffing_request:read", "shift_need:read"),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            shift_need_id=SHIFT_ID,
            command_id=COMMAND_ID,
            body=review_body(),
            now=NOW,
        )
    assert error.value.status == 403


def test_submit_shift_need_for_review_replays_matching_command():
    existing = {
        "command_id": COMMAND_ID,
        "shift_need_id": SHIFT_ID,
        "employer_id": EMPLOYER_ID,
        "staffing_request_id": REQUEST_ID,
        "actor_id": ACTOR_ID,
        "event_type": "shift_need.submitted_for_review",
        "new_version": 2,
    }
    detail = shift_detail(shift_status="pending_review", version=2)
    session = FakeSession([FakeResult(existing), FakeResult(detail)])

    result = submit_shift_need_for_review(
        session=session,  # type: ignore[arg-type]
        principal=all_permissions(),
        employer_id=EMPLOYER_ID,
        request_id=REQUEST_ID,
        shift_need_id=SHIFT_ID,
        command_id=COMMAND_ID,
        body=review_body(),
        now=NOW,
    )

    assert result.replayed is True
    assert result.payload["current"] == detail
    assert result.payload["result_record_version"] == 2
    assert session.commits == 0


def test_submit_shift_need_for_review_rejects_command_reuse_for_another_child():
    session = FakeSession(
        [
            FakeResult(
                {
                    "command_id": COMMAND_ID,
                    "shift_need_id": UUID("99999999-9999-4999-8999-999999999999"),
                    "employer_id": EMPLOYER_ID,
                    "staffing_request_id": REQUEST_ID,
                    "actor_id": ACTOR_ID,
                    "event_type": "shift_need.submitted_for_review",
                    "new_version": 2,
                }
            )
        ]
    )

    with pytest.raises(IntakeError) as error:
        submit_shift_need_for_review(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            shift_need_id=SHIFT_ID,
            command_id=COMMAND_ID,
            body=review_body(),
            now=NOW,
        )

    assert error.value.status == 409
    assert session.rollbacks == 1


@pytest.mark.parametrize(
    ("row_changes", "expected_status"),
    [
        ({"shift_status": "pending_review"}, 409),
        ({"starts_at": datetime(2026, 10, 1, 17, 0, tzinfo=UTC)}, 422),
        ({"time_zone": "Atlantis/Golden_Rose"}, 422),
    ],
)
def test_submit_shift_need_for_review_rejects_invalid_review_state(row_changes, expected_status):
    row = {
        "shift_status": "draft",
        "version": 1,
        "starts_at": datetime(2026, 10, 1, 13, 0, tzinfo=UTC),
        "ends_at": datetime(2026, 10, 1, 17, 0, tzinfo=UTC),
        "time_zone": "America/New_York",
        "request_status": "draft",
        "request_version": 2,
    }
    row.update(row_changes)
    session = FakeSession([FakeResult(None), FakeResult(row)])

    with pytest.raises(IntakeError) as error:
        submit_shift_need_for_review(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            shift_need_id=SHIFT_ID,
            command_id=COMMAND_ID,
            body=review_body(),
            now=NOW,
        )

    assert error.value.status == expected_status
    assert session.rollbacks == 1


def test_submit_shift_need_for_review_reports_missing_detail_after_write():
    session = FakeSession(
        [
            FakeResult(None),
            FakeResult(
                {
                    "shift_status": "draft",
                    "version": 1,
                    "starts_at": datetime(2026, 10, 1, 13, 0, tzinfo=UTC),
                    "ends_at": datetime(2026, 10, 1, 17, 0, tzinfo=UTC),
                    "time_zone": "America/New_York",
                    "request_status": "draft",
                    "request_version": 2,
                }
            ),
            FakeResult(),
            FakeResult(),
            FakeResult(None),
        ]
    )

    with pytest.raises(IntakeError) as error:
        submit_shift_need_for_review(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            shift_need_id=SHIFT_ID,
            command_id=COMMAND_ID,
            body=review_body(),
            now=NOW,
        )

    assert error.value.status == 404
    assert session.rollbacks == 1


def test_submit_shift_need_for_review_rolls_back_persistence_errors():
    session = FakeSession([SQLAlchemyError("database unavailable")])

    with pytest.raises(IntakeError) as error:
        submit_shift_need_for_review(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            shift_need_id=SHIFT_ID,
            command_id=COMMAND_ID,
            body=review_body(),
            now=NOW,
        )

    assert error.value.status == 503
    assert session.rollbacks == 1


def test_submit_shift_need_for_review_rejects_stale_version():
    session = FakeSession(
        [
            FakeResult(None),
            FakeResult(
                {
                    "shift_status": "draft",
                    "version": 2,
                    "starts_at": datetime(2026, 10, 1, 13, 0, tzinfo=UTC),
                    "ends_at": datetime(2026, 10, 1, 17, 0, tzinfo=UTC),
                    "time_zone": "America/New_York",
                    "request_status": "draft",
                    "request_version": 2,
                }
            ),
        ]
    )

    with pytest.raises(IntakeError) as error:
        submit_shift_need_for_review(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            shift_need_id=SHIFT_ID,
            command_id=COMMAND_ID,
            body=review_body(expected_version=1),
            now=NOW,
        )

    assert error.value.status == 412
    assert session.rollbacks == 1
    assert session.commits == 0


def test_submit_staffing_request_for_review_replays_matching_command():
    existing = {
        "command_id": COMMAND_ID,
        "staffing_request_id": REQUEST_ID,
        "employer_id": EMPLOYER_ID,
        "actor_id": ACTOR_ID,
        "event_type": "staffing_request.submitted_for_review",
        "new_version": 3,
    }
    detail = request_detail()
    session = FakeSession([FakeResult(existing), FakeResult(detail)])

    result = submit_staffing_request_for_review(
        session=session,  # type: ignore[arg-type]
        principal=all_permissions(),
        employer_id=EMPLOYER_ID,
        request_id=REQUEST_ID,
        command_id=COMMAND_ID,
        body=review_body(expected_version=2),
        now=NOW,
    )

    assert result.replayed is True
    assert result.payload["current"] == detail
    assert result.payload["result_record_version"] == 3
    assert session.commits == 0


def test_submit_staffing_request_for_review_rejects_command_reuse_for_another_request():
    session = FakeSession(
        [
            FakeResult(
                {
                    "command_id": COMMAND_ID,
                    "staffing_request_id": UUID("99999999-9999-4999-8999-999999999999"),
                    "employer_id": EMPLOYER_ID,
                    "actor_id": ACTOR_ID,
                    "event_type": "staffing_request.submitted_for_review",
                    "new_version": 3,
                }
            )
        ]
    )

    with pytest.raises(IntakeError) as error:
        submit_staffing_request_for_review(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            command_id=COMMAND_ID,
            body=review_body(expected_version=2),
            now=NOW,
        )

    assert error.value.status == 409
    assert session.rollbacks == 1


@pytest.mark.parametrize(
    ("results", "expected_status"),
    [
        ([FakeResult(None), FakeResult(None)], 404),
        ([FakeResult(None), FakeResult({"request_status": "pending_review", "version": 2})], 409),
        ([FakeResult(None), FakeResult({"request_status": "draft", "version": 3})], 412),
    ],
)
def test_submit_staffing_request_for_review_rejects_invalid_parent_state(results, expected_status):
    session = FakeSession(results)

    with pytest.raises(IntakeError) as error:
        submit_staffing_request_for_review(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            command_id=COMMAND_ID,
            body=review_body(expected_version=2),
            now=NOW,
        )

    assert error.value.status == expected_status
    assert session.rollbacks == 1


def test_submit_staffing_request_for_review_requires_pending_review_shift():
    session = FakeSession(
        [FakeResult(None), FakeResult({"request_status": "draft", "version": 2}), FakeResult(None)]
    )

    with pytest.raises(IntakeError) as error:
        submit_staffing_request_for_review(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            command_id=COMMAND_ID,
            body=review_body(expected_version=2),
            now=NOW,
        )

    assert error.value.status == 422
    assert session.rollbacks == 1


def test_submit_staffing_request_for_review_rolls_back_persistence_errors():
    session = FakeSession([SQLAlchemyError("database unavailable")])

    with pytest.raises(IntakeError) as error:
        submit_staffing_request_for_review(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
            employer_id=EMPLOYER_ID,
            request_id=REQUEST_ID,
            command_id=COMMAND_ID,
            body=review_body(expected_version=2),
            now=NOW,
        )

    assert error.value.status == 503
    assert session.rollbacks == 1


def test_submit_staffing_request_for_review_records_transition_event():
    detail = request_detail()
    session = FakeSession(
        [
            FakeResult(None),
            FakeResult({"request_status": "draft", "version": 2}),
            FakeResult({"shift_need_id": SHIFT_ID}),
            FakeResult(),
            FakeResult(),
            FakeResult(detail),
        ]
    )

    result = submit_staffing_request_for_review(
        session=session,  # type: ignore[arg-type]
        principal=all_permissions(),
        employer_id=EMPLOYER_ID,
        request_id=REQUEST_ID,
        command_id=COMMAND_ID,
        body=review_body(expected_version=2),
        now=NOW,
    )

    assert result.replayed is False
    assert result.payload["event_type"] == "staffing_request.submitted_for_review"
    assert result.payload["result_record_version"] == 3
    assert result.payload["current"] == detail
    assert session.commits == 1
    assert len(session.executed) == 6
