from typing import Protocol
from uuid import UUID


class IdentifierFactory(Protocol):
    def new_uuid4(self) -> UUID: ...
