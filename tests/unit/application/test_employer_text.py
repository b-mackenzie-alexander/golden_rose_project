import pytest

from golden_rose.application.employer_text import (
    normalize_employer_text,
    validate_employer_display_name,
)


def test_normalize_employer_text_returns_trimmed_nfc() -> None:
    assert normalize_employer_text("  Cafe\u0301  Staffing  ") == "Café  Staffing"


def test_validate_employer_display_name_rejects_blank_overlength_and_control_characters() -> None:
    with pytest.raises(ValueError, match="display_name must not be blank"):
        validate_employer_display_name("   ")

    with pytest.raises(ValueError, match="display_name must be 200 characters or fewer"):
        validate_employer_display_name("x" * 201)

    with pytest.raises(ValueError, match="display_name must not contain control characters"):
        validate_employer_display_name("Bad\nName")


def test_validate_employer_display_name_returns_trimmed_nfc_value() -> None:
    assert validate_employer_display_name("  Cafe\u0301 Revision  ") == "Café Revision"
