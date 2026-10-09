"""Idempotent private develop presentation seed data."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_schemas import CreateIntakeRequest
from golden_rose.application.intake_commands import execute_intake
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.config import Settings

DEMO_INTAKE_PERMISSIONS = frozenset(
    {
        "intake:read",
        "intake:draft:create",
        "intake:draft:revise",
        "intake:review",
        "intake:follow_up",
        "intake:restricted_history:read",
        "work_interest:read",
        "work_interest:manage",
        "worker_residence:read",
        "worker_residence:write",
        "party_address:read",
        "party_address:write",
        "worksite_address:read",
        "worksite_address:write",
        "calendar_import:manage",
    }
)


@dataclass(frozen=True, slots=True)
class SeedRecord:
    key: str
    kind: str
    content: dict[str, Any]


class _SeedClock:
    def __init__(self, instant: datetime) -> None:
        self._instant = instant

    def now(self) -> datetime:
        return self._instant


def _worker_content(
    name: str,
    index: int,
    *,
    complete: bool,
    role: str,
) -> dict[str, Any]:
    content: dict[str, Any] = {
        "full_name": name,
        "phone": f"+1 917 555 {1000 + index:04d}",
        "interests": {"other_description": role},
    }
    if complete:
        content.update(
            {
                "availability": {
                    "mode": "weekly",
                    "time_zone": "America/New_York",
                    "ranges": [
                        {
                            "weekday": (index % 5) + 1,
                            "start_local": "08:00",
                            "end_local": "16:00",
                            "end_day_offset": 0,
                        }
                    ],
                },
                "residential_address": {
                    "line1": f"{120 + index} East {20 + index % 70}th Street",
                    "locality": "New York",
                    "region": "NY",
                    "postal_code": f"10{100 + index:03d}",
                    "country": "US",
                },
            }
        )
    elif index % 2 == 0:
        content["availability"] = {"mode": "flexible"}
    return content


def _employer_content(
    name: str,
    index: int,
    *,
    complete: bool,
    role_title: str,
    duties: str,
) -> dict[str, Any]:
    content: dict[str, Any] = {
        "employer_type": "business" if index % 4 else "household",
        "display_name": name,
        "representative_name": _REPRESENTATIVES[index % len(_REPRESENTATIVES)],
        "phone": f"+1 212 555 {2000 + index:04d}",
        "role_title": role_title,
        "duties_summary": duties,
        "worker_count": (index % 4) + 1,
        "offer": {
            "minimum": str(19 + (index % 7)),
            "currency": "USD",
            "basis": "hour",
            "per_worker": True,
            "negotiable": index % 3 == 0,
        },
    }
    if complete:
        content.update(
            {
                "schedule": {
                    "mode": "specified",
                    "requested_start_date": f"2026-10-{(index % 20) + 1:02d}",
                },
                "party_address": {
                    "line1": f"{300 + index} Broadway",
                    "locality": "New York",
                    "region": "NY",
                    "postal_code": f"100{index % 90:02d}",
                    "country": "US",
                },
                "worksite_address": {
                    "line1": f"{50 + index} Queens Boulevard",
                    "locality": "Queens",
                    "region": "NY",
                    "postal_code": f"111{index % 10:02d}",
                    "country": "US",
                },
            }
        )
    else:
        content["schedule"] = {"mode": "to_be_discussed"}
    return content


_WORKER_NAMES = [
    "Ana Quispe",
    "Carlos Mendoza",
    "Maria Lopez",
    "Sofia Diaz",
    "Luis Hernandez",
    "Camila Rivera",
    "Jorge Castillo",
    "Valeria Soto",
    "Diego Morales",
    "Isabel Rojas",
    "Elena Garcia",
    "Miguel Santos",
    "Paola Vargas",
    "Rafael Nunez",
    "Lucia Herrera",
    "Nicolas Vega",
    "Gabriela Cruz",
    "Mateo Flores",
    "Adriana Pineda",
    "Oscar Medina",
    "Natalia Reyes",
    "Andres Cabrera",
    "Diana Salazar",
    "Pablo Jimenez",
    "Claudia Munoz",
    "Fernando Acosta",
    "Rosa Delgado",
    "Emilio Navarro",
    "Patricia Leon",
    "Samuel Ortega",
    "Marina Campos",
    "Victor Serrano",
    "Teresa Aguilar",
    "Hector Molina",
    "Daniela Fuentes",
    "Alberto Prieto",
    "Yasmin Romero",
    "Roberto Ibarra",
    "Liliana Arias",
    "Esteban Ponce",
    "Marta Solis",
    "Julio Benitez",
    "Andrea Luna",
    "Cesar Valdez",
    "Noemi Rivas",
    "Ricardo Alfaro",
    "Lorena Cardenas",
    "Ivan Peralta",
    "Beatriz Suarez",
    "Martin Calderon",
]

_WORKER_ROLES = [
    "Home health aide",
    "Child care assistant",
    "Kitchen assistant",
    "Office support",
    "Housekeeping",
    "Warehouse support",
    "Retail associate",
    "Companion care",
]

_EMPLOYER_NAMES = [
    "Restaurante La Esperanza",
    "Bright Horizons Staffing",
    "Clean Homes LLC",
    "Riverside Family Care",
    "Greenpoint Market",
    "Harlem Community Kitchen",
    "Astoria Senior Support",
    "Sunrise Bakery",
    "Brooklyn Family Services",
    "Queens Home Help",
    "Hudson River Cafe",
    "Uptown Child Care",
    "Morningside Housekeeping",
    "Jackson Heights Grocers",
    "Park Slope Wellness",
    "East River Catering",
    "Washington Heights Pharmacy",
    "Prospect Heights Deli",
    "Sunnyside Laundry",
    "Bronx Family Residence",
    "Chelsea Event Services",
    "Long Island City Studio",
    "Bay Ridge Medical Office",
    "Inwood Senior Residence",
    "Forest Hills Retail Group",
    "Flatbush Community Center",
    "NoHo Hospitality Group",
    "Woodside Home Care",
    "Mott Haven Kitchen",
    "Tribeca Family Office",
]

_REPRESENTATIVES = [
    "Elena Martinez",
    "Ramon Castillo",
    "Clara Benitez",
    "Henry Alvarez",
    "Julia Fernandez",
    "Monica Reyes",
]

_EMPLOYER_ROLES = [
    ("Home care aide", "Support daily household routines, meal preparation and light cleaning."),
    ("Kitchen prep worker", "Prepare ingredients, keep stations clean and support lunch service."),
    ("Child care assistant", "Assist with after-school supervision, snacks and activity setup."),
    ("Front desk assistant", "Welcome visitors, answer calls and organize appointment paperwork."),
    ("Housekeeper", "Maintain guest rooms, laundry areas and shared spaces during morning shifts."),
    (
        "Stock associate",
        "Receive deliveries, organize shelves and prepare weekly inventory counts.",
    ),
]


def presentation_seed_records() -> list[SeedRecord]:
    workers = [
        SeedRecord(
            key=f"worker-{index:02d}",
            kind="worker",
            content=_worker_content(
                name,
                index,
                complete=index >= 12,
                role=_WORKER_ROLES[index % len(_WORKER_ROLES)],
            ),
        )
        for index, name in enumerate(_WORKER_NAMES)
    ]
    employers = [
        SeedRecord(
            key=f"employer-{index:02d}",
            kind="employer",
            content=_employer_content(
                name,
                index,
                complete=index >= 8,
                role_title=_EMPLOYER_ROLES[index % len(_EMPLOYER_ROLES)][0],
                duties=_EMPLOYER_ROLES[index % len(_EMPLOYER_ROLES)][1],
            ),
        )
        for index, name in enumerate(_EMPLOYER_NAMES)
    ]
    return [*workers, *employers]


def _command_id(settings: Settings, record: SeedRecord) -> UUID:
    if settings.synthetic_staff_id is None:
        msg = "presentation demo seed requires a synthetic staff actor"
        raise RuntimeError(msg)
    return uuid5(
        NAMESPACE_URL,
        f"golden-rose:presentation-demo:{settings.synthetic_staff_id}:{record.key}",
    )


def seed_presentation_demo_data(engine: Engine, settings: Settings) -> None:
    if not settings.presentation_demo_seed_enabled:
        return
    if settings.environment != "develop" or settings.auth_mode != "synthetic":
        msg = "presentation demo seed is restricted to private synthetic develop"
        raise RuntimeError(msg)
    if settings.synthetic_staff_id is None:
        msg = "presentation demo seed requires a synthetic staff actor"
        raise RuntimeError(msg)
    principal = StaffPrincipal(
        actor_id=settings.synthetic_staff_id,
        role_name="synthetic_demo_staff",
        permissions=DEMO_INTAKE_PERMISSIONS,
    )
    created_at = datetime.now(UTC)
    with Session(engine) as session:
        for index, record in enumerate(presentation_seed_records()):
            request = CreateIntakeRequest.model_validate(
                {"kind": record.kind, "content": record.content}
            )
            execute_intake(
                session=session,
                principal=principal,
                command_id=_command_id(settings, record),
                request=request,
                clock=_SeedClock(created_at - timedelta(minutes=index)),
            )
