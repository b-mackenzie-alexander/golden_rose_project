"""Strict, partial candidate values for staff intake; no canonical defaults."""

import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator, model_validator

# Pinned ISO alphabetic code snapshots. No runtime catalog/network dependency.
# Country set: UN M49 ISO-alpha2 table, retrieved 2026-09-14, plus ISO TW.
# https://unstats.un.org/unsd/methodology/m49/overview/
# https://www.iso.org/obp/ui/#iso:code:3166:TW
COUNTRIES = frozenset(
    [
        "AD",
        "AE",
        "AF",
        "AG",
        "AI",
        "AL",
        "AM",
        "AO",
        "AQ",
        "AR",
        "AS",
        "AT",
        "AU",
        "AW",
        "AX",
        "AZ",
        "BA",
        "BB",
        "BD",
        "BE",
        "BF",
        "BG",
        "BH",
        "BI",
        "BJ",
        "BL",
        "BM",
        "BN",
        "BO",
        "BQ",
        "BR",
        "BS",
        "BT",
        "BV",
        "BW",
        "BY",
        "BZ",
        "CA",
        "CC",
        "CD",
        "CF",
        "CG",
        "CH",
        "CI",
        "CK",
        "CL",
        "CM",
        "CN",
        "CO",
        "CR",
        "CU",
        "CV",
        "CW",
        "CX",
        "CY",
        "CZ",
        "DE",
        "DJ",
        "DK",
        "DM",
        "DO",
        "DZ",
        "EC",
        "EE",
        "EG",
        "EH",
        "ER",
        "ES",
        "ET",
        "FI",
        "FJ",
        "FK",
        "FM",
        "FO",
        "FR",
        "GA",
        "GB",
        "GD",
        "GE",
        "GF",
        "GG",
        "GH",
        "GI",
        "GL",
        "GM",
        "GN",
        "GP",
        "GQ",
        "GR",
        "GS",
        "GT",
        "GU",
        "GW",
        "GY",
        "HK",
        "HM",
        "HN",
        "HR",
        "HT",
        "HU",
        "ID",
        "IE",
        "IL",
        "IM",
        "IN",
        "IO",
        "IQ",
        "IR",
        "IS",
        "IT",
        "JE",
        "JM",
        "JO",
        "JP",
        "KE",
        "KG",
        "KH",
        "KI",
        "KM",
        "KN",
        "KP",
        "KR",
        "KW",
        "KY",
        "KZ",
        "LA",
        "LB",
        "LC",
        "LI",
        "LK",
        "LR",
        "LS",
        "LT",
        "LU",
        "LV",
        "LY",
        "MA",
        "MC",
        "MD",
        "ME",
        "MF",
        "MG",
        "MH",
        "MK",
        "ML",
        "MM",
        "MN",
        "MO",
        "MP",
        "MQ",
        "MR",
        "MS",
        "MT",
        "MU",
        "MV",
        "MW",
        "MX",
        "MY",
        "MZ",
        "NA",
        "NC",
        "NE",
        "NF",
        "NG",
        "NI",
        "NL",
        "NO",
        "NP",
        "NR",
        "NU",
        "NZ",
        "OM",
        "PA",
        "PE",
        "PF",
        "PG",
        "PH",
        "PK",
        "PL",
        "PM",
        "PN",
        "PR",
        "PS",
        "PT",
        "PW",
        "PY",
        "QA",
        "RE",
        "RO",
        "RS",
        "RU",
        "RW",
        "SA",
        "SB",
        "SC",
        "SD",
        "SE",
        "SG",
        "SH",
        "SI",
        "SJ",
        "SK",
        "SL",
        "SM",
        "SN",
        "SO",
        "SR",
        "SS",
        "ST",
        "SV",
        "SX",
        "SY",
        "SZ",
        "TC",
        "TD",
        "TF",
        "TG",
        "TH",
        "TJ",
        "TK",
        "TL",
        "TM",
        "TN",
        "TO",
        "TR",
        "TT",
        "TV",
        "TW",
        "TZ",
        "UA",
        "UG",
        "UM",
        "US",
        "UY",
        "UZ",
        "VA",
        "VC",
        "VE",
        "VG",
        "VI",
        "VN",
        "VU",
        "WF",
        "WS",
        "YE",
        "YT",
        "ZA",
        "ZM",
        "ZW",
    ]
)
US_REGION_CODES = frozenset(
    [
        "AK",
        "AL",
        "AR",
        "AS",
        "AZ",
        "CA",
        "CO",
        "CT",
        "DC",
        "DE",
        "FL",
        "GA",
        "GU",
        "HI",
        "IA",
        "ID",
        "IL",
        "IN",
        "KS",
        "KY",
        "LA",
        "MA",
        "MD",
        "ME",
        "MI",
        "MN",
        "MO",
        "MP",
        "MS",
        "MT",
        "NC",
        "ND",
        "NE",
        "NH",
        "NJ",
        "NM",
        "NV",
        "NY",
        "OH",
        "OK",
        "OR",
        "PA",
        "PR",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UM",
        "UT",
        "VA",
        "VI",
        "VT",
        "WA",
        "WI",
        "WV",
        "WY",
    ]
)
US_REGION_ALIASES = {
    "new york": "NY",
}
# Source: SIX ISO 4217 List One, Pblshd 2026-01-01; retrieved 2026-09-14.
# https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/lists/list-one.xml
CURRENCIES = frozenset(
    [
        "AED",
        "AFN",
        "ALL",
        "AMD",
        "AOA",
        "ARS",
        "AUD",
        "AWG",
        "AZN",
        "BAM",
        "BBD",
        "BDT",
        "BHD",
        "BIF",
        "BMD",
        "BND",
        "BOB",
        "BOV",
        "BRL",
        "BSD",
        "BTN",
        "BWP",
        "BYN",
        "BZD",
        "CAD",
        "CDF",
        "CHE",
        "CHF",
        "CHW",
        "CLF",
        "CLP",
        "CNY",
        "COP",
        "COU",
        "CRC",
        "CUP",
        "CVE",
        "CZK",
        "DJF",
        "DKK",
        "DOP",
        "DZD",
        "EGP",
        "ERN",
        "ETB",
        "EUR",
        "FJD",
        "FKP",
        "GBP",
        "GEL",
        "GHS",
        "GIP",
        "GMD",
        "GNF",
        "GTQ",
        "GYD",
        "HKD",
        "HNL",
        "HTG",
        "HUF",
        "IDR",
        "ILS",
        "INR",
        "IQD",
        "IRR",
        "ISK",
        "JMD",
        "JOD",
        "JPY",
        "KES",
        "KGS",
        "KHR",
        "KMF",
        "KPW",
        "KRW",
        "KWD",
        "KYD",
        "KZT",
        "LAK",
        "LBP",
        "LKR",
        "LRD",
        "LSL",
        "LYD",
        "MAD",
        "MDL",
        "MGA",
        "MKD",
        "MMK",
        "MNT",
        "MOP",
        "MRU",
        "MUR",
        "MVR",
        "MWK",
        "MXN",
        "MXV",
        "MYR",
        "MZN",
        "NAD",
        "NGN",
        "NIO",
        "NOK",
        "NPR",
        "NZD",
        "OMR",
        "PAB",
        "PEN",
        "PGK",
        "PHP",
        "PKR",
        "PLN",
        "PYG",
        "QAR",
        "RON",
        "RSD",
        "RUB",
        "RWF",
        "SAR",
        "SBD",
        "SCR",
        "SDG",
        "SEK",
        "SGD",
        "SHP",
        "SLE",
        "SOS",
        "SRD",
        "SSP",
        "STN",
        "SVC",
        "SYP",
        "SZL",
        "THB",
        "TJS",
        "TMT",
        "TND",
        "TOP",
        "TRY",
        "TTD",
        "TWD",
        "TZS",
        "UAH",
        "UGX",
        "USD",
        "USN",
        "UYI",
        "UYU",
        "UYW",
        "UZS",
        "VED",
        "VES",
        "VND",
        "VUV",
        "WST",
        "XAD",
        "XAF",
        "XAG",
        "XAU",
        "XBA",
        "XBB",
        "XBC",
        "XBD",
        "XCD",
        "XCG",
        "XDR",
        "XOF",
        "XPD",
        "XPF",
        "XPT",
        "XSU",
        "XTS",
        "XUA",
        "XXX",
        "YER",
        "ZAR",
        "ZMW",
        "ZWG",
    ]
)


def normalize_text(value: str) -> str:
    if any(unicodedata.category(char).startswith("C") for char in value):
        raise ValueError("Control characters are forbidden")
    value = unicodedata.normalize("NFC", value).strip()
    if not value:
        raise ValueError("Blank text is forbidden")
    return value


Text2 = Annotated[str, Field(strict=True), AfterValidator(normalize_text), Field(max_length=2)]
Text3 = Annotated[str, Field(strict=True), AfterValidator(normalize_text), Field(max_length=3)]
Text32 = Annotated[str, Field(strict=True), AfterValidator(normalize_text), Field(max_length=32)]
Text100 = Annotated[str, Field(strict=True), AfterValidator(normalize_text), Field(max_length=100)]
Text200 = Annotated[str, Field(strict=True), AfterValidator(normalize_text), Field(max_length=200)]
Text500 = Annotated[str, Field(strict=True), AfterValidator(normalize_text), Field(max_length=500)]
Text1000 = Annotated[
    str, Field(strict=True), AfterValidator(normalize_text), Field(max_length=1000)
]


class IntakeValue(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    def to_content(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude_unset=True)


class Address(IntakeValue):
    line1: Text200 | None = None
    line2: Text200 | None = None
    locality: Text100 | None = None
    region: Text100 | None = None
    postal_code: Text32 | None = None
    country: Text2 | None = None

    @model_validator(mode="after")
    def validate_country(self) -> "Address":
        if self.country is not None and self.country not in COUNTRIES:
            raise ValueError("Invalid country")
        if self.country == "US":
            if self.region is not None:
                normalized_region = (
                    US_REGION_ALIASES.get(" ".join(self.region.lower().replace(".", " ").split()))
                    or self.region.upper()
                )
                if normalized_region not in US_REGION_CODES:
                    raise ValueError("Invalid US state or territory")
                self.region = normalized_region
            if self.postal_code is not None:
                match = re.fullmatch(r"([0-9]{5})(?:[- ]?([0-9]{4}))?", self.postal_code)
                if not match:
                    raise ValueError("Invalid US ZIP code")
                self.postal_code = (
                    match.group(1)
                    if match.group(2) is None
                    else f"{match.group(1)}-{match.group(2)}"
                )
        return self


def phone(value: str) -> str:
    value = normalize_text(value)
    match = re.fullmatch(r"\+?[0-9 ()-]+(?:(?:\s*(?:ext\.?|x)\s*)([0-9]{1,6}))?", value, re.I)
    if not 3 <= len(value) <= 40 or not match:
        raise ValueError("Invalid phone")
    main = re.split(r"ext\.?|x", value, flags=re.I)[0]
    if not 7 <= sum(c.isdigit() for c in main) <= 15:
        raise ValueError("Invalid phone digit count")
    return value


Phone = Annotated[str, Field(strict=True), AfterValidator(phone)]


def money(value: str) -> str:
    if not re.fullmatch(r"(?:0|[1-9][0-9]{0,8})(?:\.[0-9]{1,2})?", value):
        raise ValueError("Invalid decimal amount")
    return value


Money = Annotated[str, Field(strict=True), AfterValidator(money)]


class Offer(IntakeValue):
    minimum: Money | None = None
    maximum: Money | None = None
    currency: Text3 | None = None
    basis: Literal["hour", "day", "week", "month", "year", "task"] | None = None
    per_worker: bool | None = None
    negotiable: bool = False
    terms: Text500 | None = None

    @model_validator(mode="after")
    def validate_offer(self) -> "Offer":
        if self.per_worker is not None and self.per_worker is not True:
            raise ValueError("Offer must be per worker")
        if self.currency is not None and self.currency not in CURRENCIES:
            raise ValueError("Invalid currency")
        if (
            self.minimum is not None
            and self.maximum is not None
            and Decimal(self.maximum) < Decimal(self.minimum)
        ):
            raise ValueError("Maximum below minimum")
        return self


def zone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise ValueError("Invalid IANA time zone") from exc
    return value


TimeZone = Annotated[str, Field(strict=True, max_length=100), AfterValidator(zone)]
LocalTime = Annotated[str, Field(strict=True, pattern=r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")]


class WeeklyRange(IntakeValue):
    weekday: int = Field(ge=1, le=7)
    start_local: LocalTime
    end_local: LocalTime
    end_day_offset: int = Field(ge=0, le=1)

    def interval(self) -> tuple[int, int]:
        start = int(self.start_local[:2]) * 60 + int(self.start_local[3:])
        end = int(self.end_local[:2]) * 60 + int(self.end_local[3:]) + self.end_day_offset * 1440
        if not 0 < end - start <= 1440:
            raise ValueError("Invalid range duration")
        base = (self.weekday - 1) * 1440
        return base + start, base + end

    @model_validator(mode="after")
    def validate_range(self) -> "WeeklyRange":
        self.interval()
        return self


class Availability(IntakeValue):
    mode: Literal["unknown", "flexible", "weekly"]
    time_zone: TimeZone | None = None
    ranges: list[WeeklyRange] | None = Field(default=None, min_length=1, max_length=28)
    exception_note: Text500 | None = None

    @model_validator(mode="after")
    def validate_availability(self) -> "Availability":
        if self.mode != "weekly":
            if self.ranges is not None:
                raise ValueError("Ranges require weekly mode")
            return self
        if not self.time_zone or not self.ranges:
            raise ValueError("Weekly mode requires zone and ranges")
        intervals = [item.interval() for item in self.ranges]
        for index, (start, end) in enumerate(intervals):
            for other_start, other_end in intervals[index + 1 :]:
                for shift in (-10080, 0, 10080):
                    if start < other_end + shift and other_start + shift < end:
                        raise ValueError("Overlapping availability")
        return self


class Schedule(IntakeValue):
    mode: Literal["unknown", "to_be_discussed", "specified"]
    requested_start_date: str | None = None
    starts_at: str | None = None
    ends_at: str | None = None
    time_zone: TimeZone | None = None
    note: Text500 | None = None

    @model_validator(mode="after")
    def validate_schedule(self) -> "Schedule":
        values = (self.starts_at, self.ends_at, self.time_zone)
        if self.mode != "specified":
            if self.requested_start_date is not None or any(v is not None for v in values):
                raise ValueError("Schedule values require specified mode")
        elif self.requested_start_date is not None:
            if any(v is not None for v in values):
                raise ValueError("Date-only and timed schedules are exclusive")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", self.requested_start_date):
                raise ValueError("Invalid date")
            date.fromisoformat(self.requested_start_date)
        else:
            if not all(values):
                raise ValueError("Timed schedule requires start, end and zone")
            if not self.starts_at or not self.ends_at or not self.time_zone:
                raise ValueError("Timed schedule requires start, end and zone")
            instants = []
            for value in (self.starts_at, self.ends_at):
                if not re.fullmatch(
                    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])",
                    value,
                ):
                    raise ValueError("Offset-aware RFC3339 instant required")
                instant = datetime.fromisoformat(value)
                try:
                    zone_offset = instant.astimezone(ZoneInfo(self.time_zone)).utcoffset()
                except OverflowError as exc:
                    raise ValueError("Instant exceeds supported date range") from exc
                if instant.utcoffset() != zone_offset:
                    raise ValueError("Time zone offset mismatch")
                instants.append(instant)
            if instants[1] <= instants[0]:
                raise ValueError("End must follow start")
        return self


class InterestSelection(IntakeValue):
    interest_id: UUID
    catalog_version: int = Field(ge=1, le=2147483647)

    @field_validator("interest_id", mode="before")
    @classmethod
    def full_uuid(cls, value: Any) -> Any:
        if isinstance(value, str):
            parsed = UUID(value)
            if str(parsed) != value.lower():
                raise ValueError("Full UUID required")
            return parsed
        return value


class Interests(IntakeValue):
    selections: list[InterestSelection] = Field(default_factory=list, max_length=20)
    other_description: Text200 | None = None

    @model_validator(mode="after")
    def unique_selections(self) -> "Interests":
        if len({item.interest_id for item in self.selections}) != len(self.selections):
            raise ValueError("Duplicate interests")
        return self


class WorkerDraftContent(IntakeValue):
    full_name: Text200 | None = None
    phone: Phone | None = None
    interests: Interests | None = None
    availability: Availability | None = None


class EmployerDraftContent(IntakeValue):
    employer_type: Literal["household", "business"] | None = None
    display_name: Text200 | None = None
    representative_name: Text200 | None = None
    phone: Phone | None = None
    role_title: Text200 | None = None
    duties_summary: Text1000 | None = None
    worker_count: int | None = Field(default=None, ge=1, le=1000)
    schedule: Schedule | None = None
    offer: Offer | None = None


class WorkerCreateContent(WorkerDraftContent):
    residential_address: Address | None = None


class EmployerCreateContent(EmployerDraftContent):
    party_address: Address | None = None
    worksite_address: Address | None = None


def validate_content(kind: str, content: Any, *, include_addresses: bool = False) -> IntakeValue:
    model: type[IntakeValue]
    if kind == "worker":
        model = WorkerCreateContent if include_addresses else WorkerDraftContent
    elif kind == "employer":
        model = EmployerCreateContent if include_addresses else EmployerDraftContent
    else:
        raise ValueError("Invalid intake kind")
    return model.model_validate(content)


def has_substantive_content(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            has_substantive_content(v)
            for key, v in value.items()
            if not (key == "mode" and v == "unknown")
        )
    if isinstance(value, list):
        return any(has_substantive_content(v) for v in value)
    return value is not None and value is not False and value != ""
