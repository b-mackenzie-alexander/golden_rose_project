"""Injected trusted staff identities; no identity provider or user administration."""

from dataclasses import dataclass
from uuid import UUID

from golden_rose.application.intake_errors import IntakeError


@dataclass(frozen=True, slots=True)
class StaffDirectoryEntry:
    staff_id: UUID
    display_name: str
    active: bool
    permissions: frozenset[str]
    intake_scope: frozenset[UUID] | None = None

    def eligible(self, intake_id: UUID, permissions: frozenset[str]) -> bool:
        return (
            self.active
            and permissions <= self.permissions
            and (self.intake_scope is None or intake_id in self.intake_scope)
        )


@dataclass(frozen=True, slots=True)
class StaffDirectory:
    entries: tuple[StaffDirectoryEntry, ...] = ()

    def resolve(
        self, staff_id: UUID, intake_id: UUID, permissions: frozenset[str]
    ) -> StaffDirectoryEntry:
        entry = next((item for item in self.entries if item.staff_id == staff_id), None)
        if entry is None or not entry.eligible(intake_id, permissions):
            raise IntakeError("invalid_request", 422)
        return entry

    def display_name(self, staff_id: UUID) -> str:
        entry = next((item for item in self.entries if item.staff_id == staff_id), None)
        return entry.display_name if entry else "Unavailable staff"
