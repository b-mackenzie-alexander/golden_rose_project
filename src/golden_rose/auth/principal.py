from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class StaffPrincipal:
    actor_id: UUID
    role_name: str
    permissions: frozenset[str]
