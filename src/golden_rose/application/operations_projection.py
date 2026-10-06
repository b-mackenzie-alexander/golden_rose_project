"""Read-only staff operations projection for dashboard modules."""

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.permissions import EMPLOYER_READ_PERMISSION, SHIFT_NEED_READ_PERMISSION
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.models import (
    employers,
    intake_finalizations,
    shift_needs,
    staffing_requests,
    worker_residences,
    worksites,
)

AREA_BUCKETS: tuple[tuple[str, str], ...] = (
    ("bronx", "Bronx"),
    ("brooklyn", "Brooklyn"),
    ("manhattan", "Manhattan"),
    ("queens", "Queens"),
    ("staten_island", "Staten Island"),
)

LOCALITY_TO_AREA: dict[str, str] = {
    "bronx": "bronx",
    "brooklyn": "brooklyn",
    "kings": "brooklyn",
    "manhattan": "manhattan",
    "new york": "manhattan",
    "new york city": "manhattan",
    "queens": "queens",
    "staten island": "staten_island",
    "richmond": "staten_island",
}

ZONE_BUCKETS: tuple[tuple[str, str, str], ...] = (
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
)

AREA_ANCHOR_ZONE: dict[str, str] = {
    "bronx": "south_bronx",
    "brooklyn": "central_brooklyn",
    "manhattan": "midtown_lower_manhattan",
    "queens": "central_queens",
    "staten_island": "north_shore_staten_island",
}

POSTAL_ZONE_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "south_bronx",
        ("10451", "10452", "10453", "10454", "10455", "10456", "10457", "10458", "10459", "10460"),
    ),
    (
        "upper_manhattan_harlem",
        (
            "10026",
            "10027",
            "10030",
            "10031",
            "10032",
            "10033",
            "10034",
            "10035",
            "10037",
            "10039",
            "10040",
        ),
    ),
    (
        "midtown_lower_manhattan",
        (
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "10007",
            "10009",
            "10010",
            "10011",
            "10012",
            "10013",
            "10014",
            "10016",
            "10017",
            "10018",
            "10019",
            "10021",
            "10022",
            "10023",
            "10024",
            "10025",
            "10028",
            "10029",
            "10036",
            "10038",
            "10044",
            "10065",
            "10069",
            "10075",
            "10128",
            "10280",
            "10282",
        ),
    ),
    (
        "northwest_queens",
        (
            "11101",
            "11102",
            "11103",
            "11104",
            "11105",
            "11106",
            "11369",
            "11370",
            "11372",
            "11373",
            "11377",
            "11378",
        ),
    ),
    (
        "central_queens",
        (
            "11354",
            "11355",
            "11356",
            "11357",
            "11358",
            "11364",
            "11365",
            "11366",
            "11367",
            "11368",
            "11374",
            "11375",
            "11379",
            "11385",
            "11415",
            "11416",
            "11417",
            "11418",
            "11419",
            "11420",
            "11421",
            "11432",
            "11433",
            "11434",
            "11435",
            "11436",
        ),
    ),
    (
        "northeast_queens",
        ("11004", "11005", "11360", "11361", "11362", "11363", "11364"),
    ),
    ("north_brooklyn", ("11201", "11205", "11206", "11211", "11221", "11222", "11237", "11249")),
    (
        "central_brooklyn",
        (
            "11203",
            "11207",
            "11208",
            "11210",
            "11212",
            "11213",
            "11216",
            "11225",
            "11226",
            "11233",
            "11236",
            "11238",
        ),
    ),
    (
        "south_brooklyn",
        (
            "11204",
            "11209",
            "11214",
            "11218",
            "11219",
            "11220",
            "11223",
            "11224",
            "11228",
            "11229",
            "11230",
            "11232",
            "11234",
            "11235",
        ),
    ),
    ("north_shore_staten_island", ("10301", "10302", "10303", "10304", "10310")),
)

POSTAL_CODE_TO_ZONE: dict[str, str] = {
    code: zone for zone, postal_codes in POSTAL_ZONE_GROUPS for code in postal_codes
}

LOCALITY_TO_ZONE: dict[str, str] = {
    "astoria": "northwest_queens",
    "bay ridge": "south_brooklyn",
    "bayside": "northeast_queens",
    "bedford stuyvesant": "central_brooklyn",
    "bronx": "south_bronx",
    "brooklyn": "central_brooklyn",
    "bushwick": "north_brooklyn",
    "central harlem": "upper_manhattan_harlem",
    "coney island": "south_brooklyn",
    "corona": "central_queens",
    "crown heights": "central_brooklyn",
    "east flatbush": "central_brooklyn",
    "elmhurst": "central_queens",
    "far rockaway": "central_queens",
    "flatbush": "central_brooklyn",
    "flushing": "northeast_queens",
    "forest hills": "central_queens",
    "greenpoint": "north_brooklyn",
    "harlem": "upper_manhattan_harlem",
    "jackson heights": "northwest_queens",
    "jamaica": "central_queens",
    "kings": "central_brooklyn",
    "long island city": "northwest_queens",
    "manhattan": "midtown_lower_manhattan",
    "new york": "midtown_lower_manhattan",
    "new york city": "midtown_lower_manhattan",
    "queens": "central_queens",
    "rego park": "central_queens",
    "richmond": "north_shore_staten_island",
    "ridgewood": "central_queens",
    "staten island": "north_shore_staten_island",
    "sunset park": "south_brooklyn",
    "washington heights": "upper_manhattan_harlem",
    "williamsburg": "north_brooklyn",
    "woodside": "northwest_queens",
}


def _empty_area_summary() -> dict[str, dict[str, int | str]]:
    return {
        key: {
            "area_key": key,
            "area_label": label,
            "request_count": 0,
            "shift_count": 0,
            "worker_slots": 0,
            "pending_review_count": 0,
        }
        for key, label in AREA_BUCKETS
    }


def _area_key(locality: object) -> str | None:
    if not isinstance(locality, str):
        return None
    normalized = " ".join(locality.strip().lower().replace("-", " ").split())
    if not normalized:
        return None
    return LOCALITY_TO_AREA.get(normalized)


def _normalized_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.strip().lower().replace("-", " ").split())
    return normalized or None


def _postal_prefix(postal_code: object) -> str | None:
    if not isinstance(postal_code, str):
        return None
    digits = "".join(character for character in postal_code.strip() if character.isdigit())
    return digits[:5] if len(digits) >= 5 else None


def _zone_key(*, locality: object, postal_code: object) -> str | None:
    postal_prefix = _postal_prefix(postal_code)
    if postal_prefix is not None and postal_prefix in POSTAL_CODE_TO_ZONE:
        return POSTAL_CODE_TO_ZONE[postal_prefix]
    normalized_locality = _normalized_text(locality)
    if normalized_locality is None:
        return None
    zone = LOCALITY_TO_ZONE.get(normalized_locality)
    if zone is not None:
        return zone
    area = LOCALITY_TO_AREA.get(normalized_locality)
    return AREA_ANCHOR_ZONE.get(area) if area is not None else None


def _empty_zone_summary() -> dict[str, dict[str, int | str]]:
    return {
        key: {
            "zone_key": key,
            "zone_label": label,
            "area_key": area_key,
            "worker_residence_count": 0,
            "worksite_count": 0,
            "request_count": 0,
            "shift_count": 0,
            "worker_slots": 0,
            "pending_review_count": 0,
        }
        for key, label, area_key in ZONE_BUCKETS
    }


def _build_zone_summary(
    *,
    request_area_rows: Sequence[Mapping[str, Any]],
    shift_area_rows: Sequence[Mapping[str, Any]],
    worker_zone_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, int | str]]:
    zones = _empty_zone_summary()
    worksites_by_zone: dict[str, set[object]] = {key: set() for key, _label, _area in ZONE_BUCKETS}

    for row in worker_zone_rows:
        key = _zone_key(locality=row.get("locality"), postal_code=row.get("postal_code"))
        if key is None:
            continue
        zones[key]["worker_residence_count"] = int(zones[key]["worker_residence_count"]) + 1

    for row in request_area_rows:
        key = _zone_key(locality=row.get("locality"), postal_code=row.get("postal_code"))
        if key is None:
            continue
        zone = zones[key]
        zone["request_count"] = int(zone["request_count"]) + 1
        worksite_id = row.get("worksite_id")
        if worksite_id is not None:
            worksites_by_zone[key].add(worksite_id)
        if row.get("request_status") == "pending_review":
            zone["pending_review_count"] = int(zone["pending_review_count"]) + 1

    for row in shift_area_rows:
        key = _zone_key(locality=row.get("locality"), postal_code=row.get("postal_code"))
        if key is None:
            continue
        zone = zones[key]
        zone["shift_count"] = int(zone["shift_count"]) + 1
        zone["worker_slots"] = int(zone["worker_slots"]) + int(row.get("worker_count") or 0)
        if row.get("shift_status") == "pending_review":
            zone["pending_review_count"] = int(zone["pending_review_count"]) + 1

    for key, worksites_for_zone in worksites_by_zone.items():
        zones[key]["worksite_count"] = len(worksites_for_zone)

    return [zones[key] for key, _label, _area in ZONE_BUCKETS]


def _build_area_and_report_summary(
    *,
    request_area_rows: Sequence[Mapping[str, Any]],
    shift_area_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, int | str]], dict[str, int]]:
    areas = _empty_area_summary()
    report = {
        "request_count": 0,
        "shift_count": 0,
        "worker_slots": 0,
        "pending_review_count": 0,
        "active_area_count": 0,
        "unmapped_request_count": 0,
    }
    for row in request_area_rows:
        report["request_count"] += 1
        key = _area_key(row.get("locality"))
        if key is None:
            report["unmapped_request_count"] += 1
            continue
        area = areas[key]
        area["request_count"] = int(area["request_count"]) + 1
        if row.get("request_status") == "pending_review":
            area["pending_review_count"] = int(area["pending_review_count"]) + 1
            report["pending_review_count"] += 1

    for row in shift_area_rows:
        report["shift_count"] += 1
        worker_slots = int(row.get("worker_count") or 0)
        report["worker_slots"] += worker_slots
        key = _area_key(row.get("locality"))
        if key is None:
            continue
        area = areas[key]
        area["shift_count"] = int(area["shift_count"]) + 1
        area["worker_slots"] = int(area["worker_slots"]) + worker_slots
        if row.get("shift_status") == "pending_review":
            area["pending_review_count"] = int(area["pending_review_count"]) + 1
            report["pending_review_count"] += 1

    area_items = [areas[key] for key, _label in AREA_BUCKETS]
    report["active_area_count"] = sum(
        1 for area in area_items if int(area["request_count"]) > 0 or int(area["shift_count"]) > 0
    )
    return area_items, report


def _build_calendar_summary(calendar_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "projected_shift_count": 0,
        "worker_slots": 0,
        "pending_review_shift_count": 0,
        "coverage_day_count": 0,
        "first_shift_starts_at": None,
        "last_shift_ends_at": None,
    }
    coverage_days: set[date] = set()
    first_shift: datetime | None = None
    last_shift: datetime | None = None
    for row in calendar_rows:
        starts_at = row.get("starts_at")
        ends_at = row.get("ends_at")
        if not isinstance(starts_at, datetime) or not isinstance(ends_at, datetime):
            continue
        if ends_at <= starts_at:
            continue
        summary["projected_shift_count"] += 1
        summary["worker_slots"] += int(row.get("worker_count") or 0)
        if row.get("shift_status") == "pending_review":
            summary["pending_review_shift_count"] += 1
        coverage_days.add(starts_at.date())
        if first_shift is None or starts_at < first_shift:
            first_shift = starts_at
        if last_shift is None or ends_at > last_shift:
            last_shift = ends_at
    summary["coverage_day_count"] = len(coverage_days)
    summary["first_shift_starts_at"] = first_shift
    summary["last_shift_ends_at"] = last_shift
    return summary


def _build_queue_summary(
    *,
    request_queue_rows: Sequence[Mapping[str, Any]],
    shift_queue_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "open_item_count": 0,
        "draft_count": 0,
        "pending_review_count": 0,
        "high_priority_count": 0,
        "oldest_item_updated_at": None,
        "newest_item_updated_at": None,
    }
    oldest_item: datetime | None = None
    newest_item: datetime | None = None

    def count_row(status: object, updated_at: object, *, high_priority: bool = False) -> None:
        nonlocal oldest_item, newest_item
        summary["open_item_count"] += 1
        if status == "draft":
            summary["draft_count"] += 1
        if status == "pending_review":
            summary["pending_review_count"] += 1
        if high_priority:
            summary["high_priority_count"] += 1
        if isinstance(updated_at, datetime):
            if oldest_item is None or updated_at < oldest_item:
                oldest_item = updated_at
            if newest_item is None or updated_at > newest_item:
                newest_item = updated_at

    for row in request_queue_rows:
        count_row(row.get("request_status"), row.get("updated_at"))
    for row in shift_queue_rows:
        status = row.get("shift_status")
        count_row(status, row.get("updated_at"), high_priority=status == "pending_review")

    summary["oldest_item_updated_at"] = oldest_item
    summary["newest_item_updated_at"] = newest_item
    return summary


def query_operations_projection(
    *,
    session: Session,
    principal: StaffPrincipal,
    page_size: int = 50,
) -> dict[str, object]:
    required = {EMPLOYER_READ_PERMISSION, "staffing_request:read", SHIFT_NEED_READ_PERMISSION}
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)
    bounded_page_size = min(max(page_size, 1), 50)
    try:
        request_rows = (
            session.execute(
                select(
                    intake_finalizations.c.intake_id.label("source_intake_id"),
                    staffing_requests.c.employer_id,
                    employers.c.display_name.label("employer_name"),
                    staffing_requests.c.staffing_request_id,
                    staffing_requests.c.request_status,
                    staffing_requests.c.role_title,
                    staffing_requests.c.worker_count,
                    staffing_requests.c.version,
                    staffing_requests.c.received_at,
                    staffing_requests.c.updated_at,
                )
                .join(employers, employers.c.employer_id == staffing_requests.c.employer_id)
                .outerjoin(
                    intake_finalizations,
                    (intake_finalizations.c.employer_id == staffing_requests.c.employer_id)
                    & (
                        intake_finalizations.c.staffing_request_id
                        == staffing_requests.c.staffing_request_id
                    ),
                )
                .where(
                    employers.c.lifecycle_status == "draft",
                    staffing_requests.c.request_status.in_(("draft", "pending_review")),
                )
                .order_by(
                    staffing_requests.c.updated_at.desc(),
                    staffing_requests.c.staffing_request_id.asc(),
                )
                .limit(bounded_page_size)
            )
            .mappings()
            .all()
        )
        shift_rows = (
            session.execute(
                select(
                    intake_finalizations.c.intake_id.label("source_intake_id"),
                    shift_needs.c.employer_id,
                    employers.c.display_name.label("employer_name"),
                    shift_needs.c.staffing_request_id,
                    shift_needs.c.shift_need_id,
                    staffing_requests.c.request_status,
                    shift_needs.c.shift_status,
                    shift_needs.c.role_title,
                    shift_needs.c.worker_count,
                    shift_needs.c.starts_at,
                    shift_needs.c.ends_at,
                    shift_needs.c.time_zone,
                    shift_needs.c.version,
                    shift_needs.c.updated_at,
                )
                .join(
                    staffing_requests,
                    (staffing_requests.c.employer_id == shift_needs.c.employer_id)
                    & (
                        staffing_requests.c.staffing_request_id == shift_needs.c.staffing_request_id
                    ),
                )
                .join(employers, employers.c.employer_id == shift_needs.c.employer_id)
                .outerjoin(
                    intake_finalizations,
                    (intake_finalizations.c.employer_id == shift_needs.c.employer_id)
                    & (
                        intake_finalizations.c.staffing_request_id
                        == shift_needs.c.staffing_request_id
                    ),
                )
                .where(
                    employers.c.lifecycle_status == "draft",
                    staffing_requests.c.request_status.in_(("draft", "pending_review")),
                    shift_needs.c.shift_status.in_(("draft", "pending_review")),
                )
                .order_by(shift_needs.c.starts_at.asc(), shift_needs.c.shift_need_id.asc())
                .limit(bounded_page_size)
            )
            .mappings()
            .all()
        )
        request_area_rows = (
            session.execute(
                select(
                    worksites.c.worksite_id,
                    worksites.c.locality,
                    worksites.c.postal_code,
                    staffing_requests.c.request_status,
                )
                .join(
                    staffing_requests,
                    (staffing_requests.c.employer_id == worksites.c.employer_id)
                    & (staffing_requests.c.worksite_id == worksites.c.worksite_id),
                )
                .join(employers, employers.c.employer_id == staffing_requests.c.employer_id)
                .where(
                    employers.c.lifecycle_status == "draft",
                    staffing_requests.c.request_status.in_(("draft", "pending_review")),
                )
                .limit(500)
            )
            .mappings()
            .all()
        )
        shift_area_rows = (
            session.execute(
                select(
                    worksites.c.locality,
                    worksites.c.postal_code,
                    shift_needs.c.shift_status,
                    shift_needs.c.worker_count,
                )
                .join(
                    staffing_requests,
                    (staffing_requests.c.employer_id == shift_needs.c.employer_id)
                    & (
                        staffing_requests.c.staffing_request_id == shift_needs.c.staffing_request_id
                    ),
                )
                .join(
                    worksites,
                    (worksites.c.employer_id == staffing_requests.c.employer_id)
                    & (worksites.c.worksite_id == staffing_requests.c.worksite_id),
                )
                .join(employers, employers.c.employer_id == shift_needs.c.employer_id)
                .where(
                    employers.c.lifecycle_status == "draft",
                    staffing_requests.c.request_status.in_(("draft", "pending_review")),
                    shift_needs.c.shift_status.in_(("draft", "pending_review")),
                )
                .limit(500)
            )
            .mappings()
            .all()
        )
        worker_zone_rows = (
            session.execute(
                select(
                    worker_residences.c.locality,
                    worker_residences.c.postal_code,
                ).limit(500)
            )
            .mappings()
            .all()
            if "worker_residence:read" in principal.permissions
            else []
        )
        shift_calendar_rows = (
            session.execute(
                select(
                    shift_needs.c.shift_status,
                    shift_needs.c.worker_count,
                    shift_needs.c.starts_at,
                    shift_needs.c.ends_at,
                )
                .join(
                    staffing_requests,
                    (staffing_requests.c.employer_id == shift_needs.c.employer_id)
                    & (
                        staffing_requests.c.staffing_request_id == shift_needs.c.staffing_request_id
                    ),
                )
                .join(employers, employers.c.employer_id == shift_needs.c.employer_id)
                .where(
                    employers.c.lifecycle_status == "draft",
                    staffing_requests.c.request_status.in_(("draft", "pending_review")),
                    shift_needs.c.shift_status.in_(("draft", "pending_review")),
                )
                .limit(500)
            )
            .mappings()
            .all()
        )
        request_queue_rows = (
            session.execute(
                select(
                    staffing_requests.c.request_status,
                    staffing_requests.c.updated_at,
                )
                .join(employers, employers.c.employer_id == staffing_requests.c.employer_id)
                .where(
                    employers.c.lifecycle_status == "draft",
                    staffing_requests.c.request_status.in_(("draft", "pending_review")),
                )
                .limit(500)
            )
            .mappings()
            .all()
        )
        shift_queue_rows = (
            session.execute(
                select(
                    shift_needs.c.shift_status,
                    shift_needs.c.updated_at,
                )
                .join(
                    staffing_requests,
                    (staffing_requests.c.employer_id == shift_needs.c.employer_id)
                    & (
                        staffing_requests.c.staffing_request_id == shift_needs.c.staffing_request_id
                    ),
                )
                .join(employers, employers.c.employer_id == shift_needs.c.employer_id)
                .where(
                    employers.c.lifecycle_status == "draft",
                    staffing_requests.c.request_status.in_(("draft", "pending_review")),
                    shift_needs.c.shift_status.in_(("draft", "pending_review")),
                )
                .limit(500)
            )
            .mappings()
            .all()
        )
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc
    area_summary, report_summary = _build_area_and_report_summary(
        request_area_rows=cast(Sequence[Mapping[str, Any]], request_area_rows),
        shift_area_rows=cast(Sequence[Mapping[str, Any]], shift_area_rows),
    )
    zone_summary = _build_zone_summary(
        request_area_rows=cast(Sequence[Mapping[str, Any]], request_area_rows),
        shift_area_rows=cast(Sequence[Mapping[str, Any]], shift_area_rows),
        worker_zone_rows=cast(Sequence[Mapping[str, Any]], worker_zone_rows),
    )
    calendar_summary = _build_calendar_summary(
        cast(Sequence[Mapping[str, Any]], shift_calendar_rows)
    )
    queue_summary = _build_queue_summary(
        request_queue_rows=cast(Sequence[Mapping[str, Any]], request_queue_rows),
        shift_queue_rows=cast(Sequence[Mapping[str, Any]], shift_queue_rows),
    )
    return {
        "request_items": [
            {
                "item_type": "staffing_request",
                **dict(row),
            }
            for row in request_rows
        ],
        "shift_items": [
            {
                "item_type": "shift_need",
                **dict(row),
            }
            for row in shift_rows
        ],
        "area_summary": area_summary,
        "zone_summary": zone_summary,
        "report_summary": report_summary,
        "calendar_summary": calendar_summary,
        "queue_summary": queue_summary,
    }
