from uuid import uuid4

from golden_rose.api.dependencies import get_staff_principal
from golden_rose.auth.permissions import (
    CREATE_DRAFT_EMPLOYER_PERMISSION,
    EMPLOYER_READ_PERMISSION,
)
from golden_rose.config import Settings


def test_synthetic_principal_has_exact_create_and_read_permissions() -> None:
    staff_id = uuid4()
    settings = Settings(
        environment="local",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=staff_id,
    )

    principal = get_staff_principal(settings)

    assert principal.actor_id == staff_id
    assert principal.role_name == "synthetic_staff"
    assert principal.permissions == frozenset(
        {CREATE_DRAFT_EMPLOYER_PERMISSION, EMPLOYER_READ_PERMISSION}
    )


def test_request_headers_cannot_grant_read_permission() -> None:
    staff_id = uuid4()
    settings = Settings(
        environment="local",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=staff_id,
    )

    principal = get_staff_principal(settings)

    assert principal.permissions == frozenset(
        {CREATE_DRAFT_EMPLOYER_PERMISSION, EMPLOYER_READ_PERMISSION}
    )
    assert not hasattr(principal, "headers")
    assert not hasattr(principal, "request_headers")
