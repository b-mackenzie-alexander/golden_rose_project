from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from golden_rose.api.staff.intake_review_schemas import (
    FollowUpIntakeRequest,
    IntakeHistoryPage,
    ReviewIntakeRequest,
)


def test_linked_history_is_admitted_by_the_http_response_schema():
    page = IntakeHistoryPage.model_validate(
        {
            "items": [
                {
                    "event_id": str(uuid4()),
                    "version": 2,
                    "content_version": 2,
                    "event_type": "intake.linked",
                    "actor_id": str(uuid4()),
                    "actor_display_name": "Fictional reviewer",
                    "occurred_at": "2026-09-15T12:00:00Z",
                }
            ],
            "next_cursor": None,
        }
    )
    assert page.items[0].event_type == "intake.linked"


def test_review_requires_complete_follow_up_shape():
    with pytest.raises(ValidationError):
        ReviewIntakeRequest.model_validate({"expected_version": 1, "outcome": "needs_follow_up"})


def test_review_rejects_client_attribution_and_follow_up_fields():
    for extra in ({"actor_display_name": "Forged"}, {"owner_staff_id": str(uuid4())}):
        with pytest.raises(ValidationError):
            ReviewIntakeRequest.model_validate(
                {"expected_version": 1, "outcome": "intake_reviewed", **extra}
            )


def test_follow_up_requires_owner_reason_and_due_instant():
    with pytest.raises(ValidationError):
        FollowUpIntakeRequest.model_validate({"expected_version": 1, "action": "attempt"})


def test_due_timezone_offset_is_validated():
    data = {
        "expected_version": 1,
        "outcome": "needs_follow_up",
        "reason_code": "other",
        "reason_text": "Fictional follow up",
        "owner_staff_id": str(uuid4()),
        "next_follow_up_at": "2026-09-14T09:00:00-05:00",
        "time_zone": "America/New_York",
    }
    with pytest.raises(ValidationError):
        ReviewIntakeRequest.model_validate(data)


def valid_followup() -> dict[str, Any]:
    return {
        "expected_version": 1,
        "action": "attempt",
        "reason_text": "Fictional follow up",
        "owner_staff_id": str(uuid4()),
        "next_follow_up_at": "2026-09-14T09:00:00-04:00",
        "time_zone": "America/New_York",
        "method": "phone",
        "outcome": "no_answer",
    }


@pytest.mark.parametrize(
    "patch",
    [
        {"expected_version": True},
        {"expected_version": "1"},
        {"expected_version": 0},
        {"next_follow_up_at": "2026-09-14 09:00:00-04:00"},
        {"next_follow_up_at": "2026-09-14T09:00:00"},
        {"next_follow_up_at": 123},
        {"next_follow_up_at": "2026-03-08T02:30:00-05:00"},
        {"time_zone": "Fictional/Invalid"},
        {"time_zone": "../UTC"},
        {"method": None},
        {"outcome": None},
        {"method": "fax"},
        {"action": "reschedule"},
        {"owner_staff_id": "invalid"},
        {"reason_text": " "},
        {"note": "x" * 513},
        {"reason_text": "hidden\nvalue"},
        {"actor_id": str(uuid4())},
        {"occurred_at": "2026-09-14T09:00:00-04:00"},
    ],
)
def test_followup_strict_boundary_rejects_invalid_values(patch):
    with pytest.raises(ValidationError):
        FollowUpIntakeRequest.model_validate({**valid_followup(), **patch})


@pytest.mark.parametrize("instant", ["2026-11-01T01:30:00-04:00", "2026-11-01T01:30:00-05:00"])
def test_followup_accepts_both_explicit_dst_overlap_instants(instant):
    request = FollowUpIntakeRequest.model_validate(
        {**valid_followup(), "next_follow_up_at": instant}
    )
    assert request.next_follow_up_at.isoformat() == instant


def test_interest_selections_are_bounded_unique_and_concrete():
    from golden_rose.application.intake_contracts import Interests

    selected = {"interest_id": str(uuid4()), "catalog_version": 1}
    assert Interests.model_validate({"selections": []}).selections == []
    for selections in [
        [selected, selected],
        [selected] * 21,
        [{**selected, "catalog_version": True}],
        [{**selected, "catalog_version": 0}],
        [{**selected, "interest_id": str(selected["interest_id"]).replace("-", "")}],
    ]:
        with pytest.raises(ValidationError):
            Interests.model_validate({"selections": selections})


def test_restricted_history_note_keeps_original_command_bound():
    from golden_rose.api.staff.intake_review_schemas import RestrictedHistoryResponse

    with pytest.raises(ValidationError):
        RestrictedHistoryResponse.model_validate({"event_id": str(uuid4()), "note": "x" * 513})
