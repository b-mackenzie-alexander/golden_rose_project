import base64
import binascii
import re
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from golden_rose.database import validate_database_role_identifier

Environment = Literal["local", "test", "develop", "production"]
AuthMode = Literal["synthetic", "staff_oidc"]
DEVELOP_DEPLOYMENT_TARGET = "gcp-develop-private-synthetic"
CONTROLLED_LIVE_DATA_STAFF_PILOT_TARGET = "controlled-live-data-staff-pilot"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GOLDEN_ROSE_",
        extra="forbid",
        hide_input_in_errors=True,
    )

    environment: Environment
    auth_mode: AuthMode
    database_url: str = Field(repr=False)
    synthetic_staff_id: UUID | None = None
    staff_oidc_issuer: str | None = None
    staff_oidc_audience: str | None = None
    staff_oidc_jwks_url: str | None = None
    deployment_target: str | None = None
    public_environment_label: str | None = None
    deployed_image_digest: str | None = None
    static_assets_path: str | None = None
    demo_access_enabled: bool = False
    demo_access_password: SecretStr | None = Field(default=None, repr=False)
    demo_access_expires_at: datetime | None = Field(default=None, repr=False)
    presentation_demo_seed_enabled: bool = False
    google_calendar_oauth_client_id: str | None = None
    google_calendar_oauth_client_secret: SecretStr | None = Field(default=None, repr=False)
    google_calendar_oauth_redirect_uri: str | None = None
    google_calendar_import_window_days: int = Field(default=14, ge=1, le=31)

    @field_validator("demo_access_password", mode="before")
    @classmethod
    def validate_demo_access_password(cls, value: Any) -> Any:
        if value is None or isinstance(value, SecretStr):
            return value
        if not isinstance(value, str) or not value or "=" in value:
            raise ValueError("demo access password must be canonical unpadded base64url")
        try:
            decoded = base64.b64decode(
                value + "=" * (-len(value) % 4),
                altchars=b"-_",
                validate=True,
            )
        except (binascii.Error, ValueError) as exc:
            raise ValueError("demo access password must be canonical unpadded base64url") from exc
        canonical = base64.urlsafe_b64encode(decoded).decode("ascii").rstrip("=")
        if len(decoded) < 32 or canonical != value:
            raise ValueError("demo access password must be canonical unpadded base64url")
        return value

    @field_validator("demo_access_expires_at", mode="before")
    @classmethod
    def validate_demo_access_expiry_format(cls, value: Any) -> Any:
        if value is None:
            return value
        if (
            not isinstance(value, str)
            or re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value) is None
        ):
            raise ValueError("demo access expiry must use strict UTC RFC 3339")
        try:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        except ValueError as exc:
            raise ValueError("demo access expiry must use strict UTC RFC 3339") from exc

    @model_validator(mode="after")
    def validate_auth_mode(self) -> "Settings":
        if self.auth_mode == "synthetic" and self.synthetic_staff_id is None:
            msg = "synthetic_staff_id is required when auth_mode is synthetic"
            raise ValueError(msg)
        if self.auth_mode == "staff_oidc":
            self._validate_staff_oidc_configuration()
        self._validate_google_calendar_oauth_configuration()
        if self.environment == "production" and (
            self.demo_access_enabled
            or self.demo_access_password is not None
            or self.demo_access_expires_at is not None
        ):
            msg = "demo access configuration is forbidden in production"
            raise ValueError(msg)
        if self.environment == "production" and self.auth_mode == "synthetic":
            msg = "synthetic auth_mode is not allowed when environment is production"
            raise ValueError(msg)
        if self.presentation_demo_seed_enabled and self.environment != "develop":
            msg = "presentation demo seed is allowed only in develop"
            raise ValueError(msg)
        if self.environment == "develop":
            if self.deployment_target != DEVELOP_DEPLOYMENT_TARGET:
                msg = (
                    "develop deployment target must be "
                    f"{DEVELOP_DEPLOYMENT_TARGET} for synthetic auth"
                )
                raise ValueError(msg)
            label = self.public_environment_label or ""
            if "non-production" not in label.lower() or "synthetic" not in label.lower():
                msg = "develop public_environment_label must state non-production synthetic use"
                raise ValueError(msg)
            if self.deployed_image_digest is None:
                msg = "develop deployed_image_digest must be set for deployment qualification"
                raise ValueError(msg)
            if not self.demo_access_enabled and (
                self.demo_access_password is not None or self.demo_access_expires_at is not None
            ):
                msg = "develop demo access gate must be enabled when credentials are configured"
                raise ValueError(msg)
            if self.demo_access_enabled and (
                self.demo_access_password is None or self.demo_access_expires_at is None
            ):
                msg = "develop demo access password and expiry must be set"
                raise ValueError(msg)
            now = datetime.now(UTC)
            if (
                self.demo_access_expires_at is not None
                and self.demo_access_expires_at > now + timedelta(days=7)
            ):
                msg = "develop demo access expiry must be no more than seven days away"
                raise ValueError(msg)
        if self.deployed_image_digest is not None:
            validate_database_role_identifier("golden_rose_runtime")
            if (
                not self.deployed_image_digest.startswith("sha256:")
                or len(self.deployed_image_digest) != 71
            ):
                msg = "deployed_image_digest must be an immutable sha256 digest"
                raise ValueError(msg)
        return self

    def _validate_staff_oidc_configuration(self) -> None:
        if self.environment not in ("test", "production"):
            msg = "staff_oidc auth_mode is allowed only for test or production"
            raise ValueError(msg)
        if self.synthetic_staff_id is not None:
            msg = "synthetic_staff_id must not be configured when auth_mode is staff_oidc"
            raise ValueError(msg)
        values = {
            "staff_oidc_issuer": self.staff_oidc_issuer,
            "staff_oidc_audience": self.staff_oidc_audience,
            "staff_oidc_jwks_url": self.staff_oidc_jwks_url,
        }
        missing = [name for name, value in values.items() if value is None or value.strip() == ""]
        if missing:
            msg = "staff_oidc auth requires " + ", ".join(missing)
            raise ValueError(msg)
        for name in ("staff_oidc_issuer", "staff_oidc_jwks_url"):
            value = values[name]
            if (
                value is None
                or not value.startswith("https://")
                or any(ch.isspace() for ch in value)
            ):
                msg = f"{name} must be an https URL"
                raise ValueError(msg)

    @property
    def google_calendar_oauth_configured(self) -> bool:
        return (
            self.google_calendar_oauth_client_id is not None
            and self.google_calendar_oauth_client_secret is not None
            and self.google_calendar_oauth_redirect_uri is not None
        )

    @property
    def controlled_live_data_staff_pilot(self) -> bool:
        return (
            self.environment == "production"
            and self.auth_mode == "staff_oidc"
            and self.deployment_target == CONTROLLED_LIVE_DATA_STAFF_PILOT_TARGET
        )

    def _validate_google_calendar_oauth_configuration(self) -> None:
        configured_values = {
            "google_calendar_oauth_client_id": self.google_calendar_oauth_client_id,
            "google_calendar_oauth_client_secret": self.google_calendar_oauth_client_secret,
            "google_calendar_oauth_redirect_uri": self.google_calendar_oauth_redirect_uri,
        }
        present = [
            name
            for name, value in configured_values.items()
            if value is not None
            and (not isinstance(value, str) or value.strip() != "")
            and (not isinstance(value, SecretStr) or value.get_secret_value().strip() != "")
        ]
        if present and len(present) != len(configured_values):
            msg = "Google Calendar OAuth requires client id, client secret and redirect URI"
            raise ValueError(msg)
        if self.google_calendar_oauth_client_id is not None:
            client_id = self.google_calendar_oauth_client_id.strip()
            if client_id == "" or any(ch.isspace() for ch in client_id):
                msg = "google_calendar_oauth_client_id must be nonblank and contain no whitespace"
                raise ValueError(msg)
            self.google_calendar_oauth_client_id = client_id
        if self.google_calendar_oauth_redirect_uri is not None:
            redirect_uri = self.google_calendar_oauth_redirect_uri.strip()
            if (
                redirect_uri == ""
                or any(ch.isspace() for ch in redirect_uri)
                or (self.environment == "production" and not redirect_uri.startswith("https://"))
                or (
                    self.environment != "production"
                    and not redirect_uri.startswith(("https://", "http://"))
                )
            ):
                msg = "google_calendar_oauth_redirect_uri must be an allowed redirect URL"
                raise ValueError(msg)
            self.google_calendar_oauth_redirect_uri = redirect_uri
