from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class StaffPrincipal:
    actor_id: UUID
    role_name: str
    permissions: frozenset[str]
    # None denotes the shared synthetic workspace. Explicit sets support bounded
    # record membership and revocation without inventing a production directory.
    intake_scope: frozenset[UUID] | None = None
