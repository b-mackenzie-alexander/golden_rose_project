import pytest

from golden_rose.application.contact_text import validate_contact_full_name


def test_validate_contact_full_name_normalizes_nfc_and_outer_whitespace() -> None:
    assert validate_contact_full_name("  Cafe\u0301 Contact  ") == "Café Contact"


def test_validate_contact_full_name_rejects_blank_control_and_over_200_scalar_values() -> None:
    with pytest.raises(ValueError, match="full_name must not be blank"):
        validate_contact_full_name("   ")

    with pytest.raises(ValueError, match="full_name must not contain control characters"):
        validate_contact_full_name("Bad\nContact")

    with pytest.raises(ValueError, match="full_name must be 200 characters or fewer"):
        validate_contact_full_name("x" * 201)


def test_contact_name_boundary_accepts_200_and_rejects_201_unicode_scalars() -> None:
    assert validate_contact_full_name("á" * 200) == "á" * 200

    with pytest.raises(ValueError, match="full_name must be 200 characters or fewer"):
        validate_contact_full_name("á" * 201)
