"""Fixed canonical correction targets and section boundaries; no transaction commit."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import Table

from golden_rose.application import canonical_correction_contracts as contracts
from golden_rose.persistence import models

ADDRESS_FIELDS = ("line1", "line2", "locality", "region", "postal_code", "country")


@dataclass(frozen=True)
class CorrectionSpec:
    entity: str
    table: Table
    model: type[contracts.CorrectionRequest]
    fields: tuple[str, ...]
    permissions: frozenset[str]
    address: bool = False


_WORKER = frozenset({"worker:read"})
_CONTACT = frozenset({"employer:read", "employer_contact:read", "employer_contact:details:read"})
SPECS = {
    "correct_worker": CorrectionSpec(
        "worker",
        models.workers,
        contracts.CorrectWorkerRequest,
        ("full_name",),
        _WORKER | {"worker:correct"},
    ),
    "correct_worker_contact": CorrectionSpec(
        "worker_contact",
        models.worker_contacts,
        contracts.CorrectWorkerContactRequest,
        ("phone", "email"),
        _WORKER | {"worker_contact:read", "worker_contact:correct"},
    ),
    "correct_worker_residence": CorrectionSpec(
        "worker_residence",
        models.worker_residences,
        contracts.CorrectWorkerResidenceRequest,
        ADDRESS_FIELDS,
        _WORKER | {"worker_residence:read", "worker_residence:write", "worker_residence:correct"},
        True,
    ),
    "correct_worker_preferences": CorrectionSpec(
        "worker_preferences",
        models.worker_preferences,
        contracts.CorrectWorkerPreferencesRequest,
        ("interests", "availability"),
        _WORKER | {"worker_preferences:correct"},
    ),
    "correct_contact_details": CorrectionSpec(
        "employer_contact_details",
        models.employer_contact_details,
        contracts.CorrectContactDetailsRequest,
        ("representative_name", "phone", "email"),
        _CONTACT | {"employer_contact:details:correct"},
    ),
    "correct_contact_address": CorrectionSpec(
        "employer_contact_details",
        models.employer_contact_details,
        contracts.CorrectContactAddressRequest,
        ADDRESS_FIELDS,
        _CONTACT
        | {"employer_contact:details:correct", "party_address:read", "party_address:write"},
        True,
    ),
    "correct_employer_address": CorrectionSpec(
        "employer_address",
        models.employer_addresses,
        contracts.CorrectEmployerAddressRequest,
        ADDRESS_FIELDS,
        frozenset(
            {
                "employer:read",
                "employer_address:correct",
                "party_address:read",
                "party_address:write",
            }
        ),
        True,
    ),
    "correct_worksite_address": CorrectionSpec(
        "worksite",
        models.worksites,
        contracts.CorrectWorksiteAddressRequest,
        ADDRESS_FIELDS,
        frozenset(
            {
                "employer:read",
                "worksite:read",
                "worksite:correct",
                "worksite_address:read",
                "worksite_address:write",
            }
        ),
        True,
    ),
    "correct_staffing_request": CorrectionSpec(
        "staffing_request",
        models.staffing_requests,
        contracts.CorrectStaffingRequestRequest,
        ("role_title", "duties_summary", "worker_count", "schedule", "offer"),
        frozenset({"employer:read", "staffing_request:read", "staffing_request:correct"}),
    ),
}


def section_snapshot(spec: CorrectionSpec, row: dict[str, Any]) -> dict[str, Any]:
    values = {name: row[name] for name in spec.fields if row[name] is not None or name == "email"}
    return {"address": values} if spec.address else values
