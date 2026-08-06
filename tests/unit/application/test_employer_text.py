from golden_rose.application.employer_text import normalize_employer_text


def test_normalize_employer_text_returns_trimmed_nfc() -> None:
    assert normalize_employer_text("  Cafe\u0301  Staffing  ") == "Café  Staffing"
