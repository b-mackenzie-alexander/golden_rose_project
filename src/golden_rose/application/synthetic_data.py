import re
from typing import Literal

from golden_rose.config import Environment

SyntheticField = Literal["employer_display_name", "contact_full_name"]

_EMPLOYER_PATTERN = re.compile(r"^Synthetic (?:Qual|Demo) Employer [0-9a-f]{8}(?: Revised)?$")
_CONTACT_PATTERN = re.compile(r"^Synthetic (?:Demo )?Contact [0-9a-f]{8}$")


class SyntheticDataAdmissionError(ValueError):
    pass


def require_develop_synthetic_value(
    *,
    environment: Environment,
    field: SyntheticField,
    value: str,
) -> None:
    if environment != "develop":
        return
    pattern = _EMPLOYER_PATTERN if field == "employer_display_name" else _CONTACT_PATTERN
    if pattern.fullmatch(value) is None:
        raise SyntheticDataAdmissionError(
            "develop accepts only generated fictional synthetic values"
        )
