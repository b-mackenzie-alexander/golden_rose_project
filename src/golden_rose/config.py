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
AuthMode = Literal["synthetic"]
DEVELOP_DEPLOYMENT_TARGET = "gcp-develop-private-synthetic"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GOLDEN_ROSE_",
        extra="forbid",
        hide_input_in_errors=True,
    )

    environment: Environment
    auth_mode: AuthMode
    database_url: str = Field(repr=False)
    synthetic_staff_id: UUID
    deployment_target: str | None = None
    public_environment_label: str | None = None
    deployed_image_digest: str | None = None
    static_assets_path: str | None = None
    demo_access_enabled: bool = False
    demo_access_password: SecretStr | None = Field(default=None, repr=False)
    demo_access_expires_at: datetime | None = Field(default=None, repr=False)
    presentation_demo_seed_enabled: bool = False

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
