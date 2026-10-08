from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import Mock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from golden_rose.api.dependencies import get_db_session, get_settings, get_staff_principal
from golden_rose.api.staff import operations
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.operations_projection import query_operations_projection
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.config import Settings
from golden_rose.main import create_app

ACTOR_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYER_ID = UUID("22222222-2222-4222-8222-222222222222")
INTAKE_ID = UUID("33333333-3333-4333-8333-333333333333")
REQUEST_ID = UUID("44444444-4444-4444-8444-444444444444")
SHIFT_ID = UUID("55555555-5555-4555-8555-555555555555")
NOW = datetime(2026, 9, 30, 14, 0, tzinfo=UTC)
ZONE_BUCKETS = [
    ("south_bronx", "South Bronx", "bronx"),
    ("upper_manhattan_harlem", "Upper Manhattan / Harlem", "manhattan"),
    ("midtown_lower_manhattan", "Midtown / Lower Manhattan", "manhattan"),
    ("northwest_queens", "Northwest Queens", "queens"),
    ("central_queens", "Central Queens", "queens"),
    ("northeast_queens", "Northeast Queens", "queens"),
    ("north_brooklyn", "North Brooklyn", "brooklyn"),
    ("central_brooklyn", "Central Brooklyn", "brooklyn"),
    ("south_brooklyn", "South Brooklyn", "brooklyn"),
    ("north_shore_staten_island", "North Shore Staten Island", "staten_island"),
]


class FakeResult:
    def __init__(self, value: Any = None) -> None:
        self.value = value

    def mappings(self) -> "FakeResult":
        return self

    def all(self) -> Any:
        return self.value


class FakeSession:
    def __init__(self, results: list[FakeResult | Exception]) -> None:
        self.results = list(results)
        self.rollbacks = 0
        self.executed: list[Any] = []

    def execute(self, statement: Any) -> FakeResult:
        self.executed.append(statement)
        if not self.results:
            return FakeResult([])
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def rollback(self) -> None:
        self.rollbacks += 1


def principal(*permissions: str) -> StaffPrincipal:
    return StaffPrincipal(ACTOR_ID, "operations_staff", frozenset(permissions))


def all_permissions() -> StaffPrincipal:
    return principal(
        "employer:read",
        "staffing_request:read",
        "shift_need:read",
        "intake:read",
        "worker_residence:read",
        "worksite_address:read",
    )


def empty_zone_summary() -> list[dict[str, object]]:
    return [
        {
            "zone_key": key,
            "zone_label": label,
            "area_key": area_key,
            "worker_residence_count": 0,
            "worksite_count": 0,
            "intake_worker_residence_count": 0,
            "intake_worksite_count": 0,
            "request_count": 0,
            "shift_count": 0,
            "worker_slots": 0,
            "pending_review_count": 0,
        }
        for key, label, area_key in ZONE_BUCKETS
    ]


def test_operations_projection_route_returns_no_store_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = create_app(engine_factory=lambda: Mock())
    app.dependency_overrides[get_db_session] = lambda: object()
    app.dependency_overrides[get_staff_principal] = all_permissions
    app.dependency_overrides[get_settings] = lambda: Settings(
        environment="test",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://golden_rose_app:test@localhost/golden_rose",
        synthetic_staff_id=ACTOR_ID,
    )
    projected = {
        "request_items": [
            {
                "item_type": "staffing_request",
                "source_intake_id": INTAKE_ID,
                "employer_id": EMPLOYER_ID,
                "employer_name": "Restaurante La Esperanza",
                "staffing_request_id": REQUEST_ID,
                "request_status": "pending_review",
                "role_title": "Line cook",
                "worker_count": 2,
                "version": 3,
                "received_at": NOW,
                "updated_at": NOW,
            }
        ],
        "shift_items": [],
        "area_summary": [
            {
                "area_key": "brooklyn",
                "area_label": "Brooklyn",
                "request_count": 1,
                "shift_count": 0,
                "worker_slots": 0,
                "pending_review_count": 1,
            }
        ],
        "zone_summary": empty_zone_summary(),
        "report_summary": {
            "request_count": 1,
            "shift_count": 0,
            "worker_slots": 0,
            "pending_review_count": 1,
            "active_area_count": 1,
            "unmapped_request_count": 0,
        },
        "calendar_summary": {
            "projected_shift_count": 0,
            "worker_slots": 0,
            "pending_review_shift_count": 0,
            "coverage_day_count": 0,
            "first_shift_starts_at": None,
            "last_shift_ends_at": None,
        },
        "queue_summary": {
            "open_item_count": 0,
            "draft_count": 0,
            "pending_review_count": 0,
            "high_priority_count": 0,
            "oldest_item_updated_at": None,
            "newest_item_updated_at": None,
        },
    }

    def fake_projection(**kwargs: Any) -> dict[str, Any]:
        assert kwargs["session"] is not None
        assert kwargs["principal"].actor_id == ACTOR_ID
        assert kwargs["page_size"] == 12
        return projected

    monkeypatch.setattr(operations, "query_operations_projection", fake_projection)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/staff/v1/operations/projection?page_size=12")

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    assert response.json()["request_items"][0]["staffing_request_id"] == str(REQUEST_ID)
    assert response.json()["shift_items"] == []
    assert response.json()["area_summary"][0]["area_label"] == "Brooklyn"
    assert response.json()["zone_summary"][0]["zone_label"] == "South Bronx"
    assert response.json()["report_summary"]["pending_review_count"] == 1
    assert response.json()["calendar_summary"]["projected_shift_count"] == 0
    assert response.json()["queue_summary"]["open_item_count"] == 0


def test_operations_projection_route_bounds_page_size() -> None:
    app = create_app(engine_factory=lambda: Mock())
    app.dependency_overrides[get_db_session] = lambda: object()
    app.dependency_overrides[get_staff_principal] = all_permissions
    app.dependency_overrides[get_settings] = lambda: Settings(
        environment="test",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://golden_rose_app:test@localhost/golden_rose",
        synthetic_staff_id=ACTOR_ID,
    )

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/staff/v1/operations/projection?page_size=51")

    assert response.status_code == 422


def test_operations_projection_requires_request_and_shift_read_permissions():
    with pytest.raises(IntakeError) as error:
        query_operations_projection(
            session=FakeSession([]),  # type: ignore[arg-type]
            principal=principal("employer:read", "staffing_request:read"),
        )

    assert error.value.status == 403


def test_operations_projection_returns_request_and_shift_items():
    request_row = {
        "source_intake_id": INTAKE_ID,
        "employer_id": EMPLOYER_ID,
        "employer_name": "Restaurante La Esperanza",
        "staffing_request_id": REQUEST_ID,
        "request_status": "pending_review",
        "role_title": "Line cook",
        "worker_count": 2,
        "version": 3,
        "received_at": NOW,
        "updated_at": NOW,
    }
    shift_row = {
        "source_intake_id": INTAKE_ID,
        "employer_id": EMPLOYER_ID,
        "employer_name": "Restaurante La Esperanza",
        "staffing_request_id": REQUEST_ID,
        "shift_need_id": SHIFT_ID,
        "request_status": "pending_review",
        "shift_status": "pending_review",
        "role_title": "Line cook",
        "worker_count": 1,
        "starts_at": NOW,
        "ends_at": datetime(2026, 9, 30, 18, 0, tzinfo=UTC),
        "time_zone": "America/New_York",
        "version": 2,
        "updated_at": NOW,
    }
    session = FakeSession(
        [
            FakeResult([request_row]),
            FakeResult([shift_row]),
            FakeResult([]),
            FakeResult([]),
            FakeResult([]),
            FakeResult([]),
            FakeResult([]),
            FakeResult([]),
        ]
    )

    result = query_operations_projection(
        session=session,  # type: ignore[arg-type]
        principal=all_permissions(),
        page_size=500,
    )

    assert result == {
        "request_items": [{"item_type": "staffing_request", **request_row}],
        "shift_items": [{"item_type": "shift_need", **shift_row}],
        "area_summary": [
            {
                "area_key": "bronx",
                "area_label": "Bronx",
                "request_count": 0,
                "shift_count": 0,
                "worker_slots": 0,
                "pending_review_count": 0,
            },
            {
                "area_key": "brooklyn",
                "area_label": "Brooklyn",
                "request_count": 0,
                "shift_count": 0,
                "worker_slots": 0,
                "pending_review_count": 0,
            },
            {
                "area_key": "manhattan",
                "area_label": "Manhattan",
                "request_count": 0,
                "shift_count": 0,
                "worker_slots": 0,
                "pending_review_count": 0,
            },
            {
                "area_key": "queens",
                "area_label": "Queens",
                "request_count": 0,
                "shift_count": 0,
                "worker_slots": 0,
                "pending_review_count": 0,
            },
            {
                "area_key": "staten_island",
                "area_label": "Staten Island",
                "request_count": 0,
                "shift_count": 0,
                "worker_slots": 0,
                "pending_review_count": 0,
            },
        ],
        "zone_summary": empty_zone_summary(),
        "report_summary": {
            "request_count": 0,
            "shift_count": 0,
            "worker_slots": 0,
            "pending_review_count": 0,
            "active_area_count": 0,
            "unmapped_request_count": 0,
        },
        "calendar_summary": {
            "projected_shift_count": 0,
            "worker_slots": 0,
            "pending_review_shift_count": 0,
            "coverage_day_count": 0,
            "first_shift_starts_at": None,
            "last_shift_ends_at": None,
        },
        "queue_summary": {
            "open_item_count": 0,
            "draft_count": 0,
            "pending_review_count": 0,
            "high_priority_count": 0,
            "oldest_item_updated_at": None,
            "newest_item_updated_at": None,
        },
    }
    assert len(session.executed) == 9
    assert session.rollbacks == 0


def test_operations_projection_aggregates_broad_area_and_reporting_totals():
    session = FakeSession(
        [
            FakeResult([]),
            FakeResult([]),
            FakeResult(
                [
                    {
                        "worksite_id": "worksite-brooklyn",
                        "locality": "Brooklyn",
                        "postal_code": "11213",
                        "request_status": "pending_review",
                    },
                    {
                        "worksite_id": "worksite-manhattan",
                        "locality": "New York",
                        "postal_code": "10018",
                        "request_status": "draft",
                    },
                    {
                        "worksite_id": "worksite-outside",
                        "locality": "Fictional City",
                        "postal_code": "99999",
                        "request_status": "pending_review",
                    },
                ]
            ),
            FakeResult(
                [
                    {
                        "locality": "Brooklyn",
                        "postal_code": "11213",
                        "shift_status": "pending_review",
                        "worker_count": 2,
                    },
                    {
                        "locality": "Queens",
                        "postal_code": "11375",
                        "shift_status": "draft",
                        "worker_count": 3,
                    },
                    {
                        "locality": "Outside",
                        "postal_code": "99999",
                        "shift_status": "draft",
                        "worker_count": 4,
                    },
                ]
            ),
            FakeResult(
                [
                    {"locality": "Crown Heights", "postal_code": "11213"},
                    {"locality": "Astoria", "postal_code": "11103"},
                ]
            ),
            FakeResult(
                [
                    {
                        "section": "worker_residence",
                        "locality": "Crown Heights",
                        "postal_code": "11213",
                    },
                    {
                        "section": "worksite_address",
                        "locality": "Brooklyn",
                        "postal_code": "11213",
                    },
                    {
                        "section": "worker_residence",
                        "locality": "Outside",
                        "postal_code": "99999",
                    },
                ]
            ),
            FakeResult(
                [
                    {
                        "shift_status": "pending_review",
                        "worker_count": 2,
                        "starts_at": NOW,
                        "ends_at": datetime(2026, 9, 30, 18, 0, tzinfo=UTC),
                    },
                    {
                        "shift_status": "draft",
                        "worker_count": 3,
                        "starts_at": datetime(2026, 10, 1, 14, 0, tzinfo=UTC),
                        "ends_at": datetime(2026, 10, 1, 18, 0, tzinfo=UTC),
                    },
                    {
                        "shift_status": "draft",
                        "worker_count": 4,
                        "starts_at": datetime(2026, 10, 1, 19, 0, tzinfo=UTC),
                        "ends_at": datetime(2026, 10, 1, 21, 0, tzinfo=UTC),
                    },
                    {
                        "shift_status": "pending_review",
                        "worker_count": 1,
                        "starts_at": "not-a-datetime",
                        "ends_at": datetime(2026, 10, 2, 18, 0, tzinfo=UTC),
                    },
                ]
            ),
            FakeResult(
                [
                    {
                        "request_status": "pending_review",
                        "updated_at": datetime(2026, 9, 29, 15, 0, tzinfo=UTC),
                    },
                    {
                        "request_status": "draft",
                        "updated_at": datetime(2026, 9, 30, 15, 0, tzinfo=UTC),
                    },
                ]
            ),
            FakeResult(
                [
                    {
                        "shift_status": "pending_review",
                        "updated_at": datetime(2026, 9, 30, 16, 0, tzinfo=UTC),
                    },
                    {
                        "shift_status": "draft",
                        "updated_at": datetime(2026, 10, 1, 16, 0, tzinfo=UTC),
                    },
                ]
            ),
        ]
    )

    result = query_operations_projection(
        session=session,  # type: ignore[arg-type]
        principal=all_permissions(),
    )

    area_items = cast(list[dict[str, object]], result["area_summary"])
    areas = {item["area_key"]: item for item in area_items}
    zone_items = cast(list[dict[str, object]], result["zone_summary"])
    zones = {item["zone_key"]: item for item in zone_items}
    assert areas["brooklyn"] == {
        "area_key": "brooklyn",
        "area_label": "Brooklyn",
        "request_count": 1,
        "shift_count": 1,
        "worker_slots": 2,
        "pending_review_count": 2,
    }
    assert areas["manhattan"]["request_count"] == 1
    assert areas["queens"]["worker_slots"] == 3
    assert zones["central_brooklyn"] == {
        "zone_key": "central_brooklyn",
        "zone_label": "Central Brooklyn",
        "area_key": "brooklyn",
        "worker_residence_count": 1,
        "worksite_count": 1,
        "intake_worker_residence_count": 1,
        "intake_worksite_count": 1,
        "request_count": 1,
        "shift_count": 1,
        "worker_slots": 2,
        "pending_review_count": 2,
    }
    assert zones["northwest_queens"]["worker_residence_count"] == 1
    assert zones["northwest_queens"]["intake_worker_residence_count"] == 0
    assert zones["central_queens"]["worker_slots"] == 3
    assert zones["midtown_lower_manhattan"]["request_count"] == 1
    assert result["report_summary"] == {
        "request_count": 3,
        "shift_count": 3,
        "worker_slots": 9,
        "pending_review_count": 2,
        "active_area_count": 3,
        "unmapped_request_count": 1,
    }
    assert result["calendar_summary"] == {
        "projected_shift_count": 3,
        "worker_slots": 9,
        "pending_review_shift_count": 1,
        "coverage_day_count": 2,
        "first_shift_starts_at": NOW,
        "last_shift_ends_at": datetime(2026, 10, 1, 21, 0, tzinfo=UTC),
    }
    assert result["queue_summary"] == {
        "open_item_count": 4,
        "draft_count": 2,
        "pending_review_count": 2,
        "high_priority_count": 1,
        "oldest_item_updated_at": datetime(2026, 9, 29, 15, 0, tzinfo=UTC),
        "newest_item_updated_at": datetime(2026, 10, 1, 16, 0, tzinfo=UTC),
    }


def test_operations_projection_rolls_back_persistence_errors():
    session = FakeSession([SQLAlchemyError("database unavailable")])

    with pytest.raises(IntakeError) as error:
        query_operations_projection(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
        )

    assert error.value.status == 503
    assert session.rollbacks == 1
