import unicodedata


def normalize_contact_full_name(value: str) -> str:
    return unicodedata.normalize("NFC", value.strip())


def validate_contact_full_name(value: str) -> str:
    normalized = normalize_contact_full_name(value)
    if not normalized:
        msg = "full_name must not be blank"
        raise ValueError(msg)
    if len(normalized) > 200:
        msg = "full_name must be 200 characters or fewer"
        raise ValueError(msg)
    if any(unicodedata.category(character).startswith("C") for character in normalized):
        msg = "full_name must not contain control characters"
        raise ValueError(msg)
    return normalized
