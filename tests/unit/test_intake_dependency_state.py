from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from golden_rose.application.intake_errors import IntakeError
from golden_rose.persistence import intake_review_state
from golden_rose.persistence.intake_dependency_state import dependencies_current


def refs(*names) -> dict[str, Any]:
    return {name: {"id": str(uuid4()), "version": 1} for name in names}


def test_unlinked_reviews_do_not_read_canonical_tables():
    session = Mock(spec=Session)
    assert dependencies_current(session, "worker", {})
    session.scalar.assert_not_called()


@pytest.mark.parametrize("version", [None, 2, 1])
def test_employer_version_controls_freshness_without_fact_reads(version):
    session = Mock(spec=Session)
    session.scalar.return_value = version
    assert dependencies_current(session, "employer", refs("employer")) == (version == 1)
    query = session.scalar.call_args.args[0]
    assert [c.name for c in query.selected_columns] == ["version"]
    assert "FOR UPDATE" not in str(query)


def test_contact_details_require_selected_parent_and_contact():
    session = Mock(spec=Session)
    session.scalar.return_value = 1
    assert dependencies_current(
        session, "employer", refs("employer", "employer_contact", "employer_contact_details")
    )
    query = str(session.scalar.call_args.args[0])
    assert "employer_contact_details.employer_id =" in query
    assert "employer_contact_details.employer_contact_id =" in query


@pytest.mark.parametrize("stale", [None, uuid4()])
def test_worker_catalog_currency_is_checked_without_reading_preferences(stale):
    session = Mock(spec=Session)
    session.scalar.side_effect = [1, 1, 1, 1, stale]
    assert dependencies_current(
        session,
        "worker",
        refs("worker", "worker_contact", "worker_residence", "worker_preferences"),
    ) == (stale is None)
    query = str(session.scalar.call_args.args[0])
    assert "worker_interest_selections" in query and "work_interests.active IS false" in query
    assert "phone" not in query and "availability" not in query


@pytest.mark.parametrize(
    "references",
    [refs("worker"), refs("employer", "worksite"), {"worker": {"id": "invalid", "version": 1}}],
)
def test_invalid_stored_shapes_fail_closed(references):
    with pytest.raises(IntakeError) as error:
        dependencies_current(Mock(spec=Session), "worker", references)
    assert error.value.status == 503


@pytest.mark.parametrize("current,expected", [(True, "current"), (False, "stale")])
def test_projection_uses_dependency_status_not_candidate_catalog(monkeypatch, current, expected):
    session = Mock(spec=Session)
    latest = {
        "review_id": uuid4(),
        "reviewed_record_version": 2,
        "reviewed_content_version": 1,
        "outcome": "intake_reviewed",
        "actor_id": uuid4(),
        "actor_display_name": "Fictional",
        "occurred_at": None,
        "dependency_refs": refs("employer"),
    }
    session.execute.return_value.mappings.return_value.one_or_none.return_value = latest
    monkeypatch.setattr(intake_review_state, "dependencies_current", Mock(return_value=current))
    monkeypatch.setattr(intake_review_state, "latest_follow_up", Mock(return_value=None))
    catalog = Mock()
    monkeypatch.setattr(intake_review_state, "selected_interests", catalog)
    state, metadata = intake_review_state.review_projection(
        session,
        {
            "intake_id": uuid4(),
            "kind": "employer",
            "content_version": 1,
            "content": {"interests": {"selections": [{}]}},
        },
    )
    assert state["review_status"] == expected
    assert metadata is not None
    assert "dependency_refs" not in metadata
    catalog.assert_not_called()
