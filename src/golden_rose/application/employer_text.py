import unicodedata


def normalize_employer_text(value: str) -> str:
    return unicodedata.normalize("NFC", value.strip())


def validate_employer_display_name(value: str) -> str:
    normalized = normalize_employer_text(value)
    if not normalized:
        msg = "display_name must not be blank"
        raise ValueError(msg)
    if len(normalized) > 200:
        msg = "display_name must be 200 characters or fewer"
        raise ValueError(msg)
    if any(unicodedata.category(character).startswith("C") for character in normalized):
        msg = "display_name must not contain control characters"
        raise ValueError(msg)
    return normalized
