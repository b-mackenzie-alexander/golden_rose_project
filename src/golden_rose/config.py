from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from golden_rose.database import validate_database_role_identifier

Environment = Literal["local", "test", "develop", "production"]
AuthMode = Literal["synthetic"]
DEVELOP_DEPLOYMENT_TARGET = "gcp-develop-private-synthetic"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GOLDEN_ROSE_",
        extra="forbid",
    )

    environment: Environment
    auth_mode: AuthMode
    database_url: str = Field(repr=False)
    synthetic_staff_id: UUID
    deployment_target: str | None = None
    public_environment_label: str | None = None
    deployed_image_digest: str | None = None
    static_assets_path: str | None = None

    @model_validator(mode="after")
    def validate_auth_mode(self) -> "Settings":
        if self.environment == "production" and self.auth_mode == "synthetic":
            msg = "synthetic auth_mode is not allowed when environment is production"
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
        if self.deployed_image_digest is not None:
            validate_database_role_identifier("golden_rose_runtime")
            if (
                not self.deployed_image_digest.startswith("sha256:")
                or len(self.deployed_image_digest) != 71
            ):
                msg = "deployed_image_digest must be an immutable sha256 digest"
                raise ValueError(msg)
        return self
