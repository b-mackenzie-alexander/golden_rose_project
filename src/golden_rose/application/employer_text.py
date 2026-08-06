import unicodedata


def normalize_employer_text(value: str) -> str:
    return unicodedata.normalize("NFC", value.strip())
