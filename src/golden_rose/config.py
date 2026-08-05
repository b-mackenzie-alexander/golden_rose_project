from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "test", "production"]
AuthMode = Literal["synthetic"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GOLDEN_ROSE_",
        extra="forbid",
    )

    environment: Environment
    auth_mode: AuthMode
    database_url: str = Field(repr=False)
    synthetic_staff_id: UUID

    @model_validator(mode="after")
    def validate_auth_mode(self) -> "Settings":
        if self.environment == "production" and self.auth_mode == "synthetic":
            msg = "synthetic auth_mode is not allowed when environment is production"
            raise ValueError(msg)
        return self
