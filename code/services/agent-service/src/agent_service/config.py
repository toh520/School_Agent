"""Validated process configuration for the Agent service."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Fail-fast environment settings shared by health and future Agent modules."""

    model_config = SettingsConfigDict(env_prefix="SCHOOL_AGENT_", case_sensitive=False)

    app_timezone: Literal["Asia/Shanghai"] = "Asia/Shanghai"
    db_host: str
    db_port: int = 5432
    db_name: str
    db_username: str
    db_password: SecretStr
    core_url: str


@lru_cache
def get_settings() -> Settings:
    """Load and validate settings once per process."""

    return Settings()  # type: ignore[call-arg]
