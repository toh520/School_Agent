"""Validated process configuration for the Agent service."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
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
    llm_provider: str = "siliconflow"
    llm_base_url: str = "https://api.siliconflow.cn/v1"
    llm_model: str = "deepseek-ai/DeepSeek-V4-Flash"
    llm_api_key: SecretStr | None = None
    llm_timeout_seconds: float = 180.0
    llm_max_retries: int = 2
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    embedding_cache_dir: str = "../../../tmp/models"
    rag_similarity_threshold: float = 0.58
    rag_top_k: int = 5
    study_material_root: str = "../../../学习资料/学习资料"
    study_courses: str = "数据结构,算法设计与分析,计算机网络"
    study_parser_version: str = "m06-v2"
    study_max_pdf_ocr_pages: int = Field(default=80, ge=1, le=500)
    upload_root: str = "../../../tmp/learning-uploads"
    upload_max_bytes: int = 20 * 1024 * 1024

    @property
    def enabled_study_courses(self) -> tuple[str, ...]:
        """Return the explicitly configured first-wave courses in stable order."""

        return tuple(item.strip() for item in self.study_courses.split(",") if item.strip())

    @property
    def llm_configured(self) -> bool:
        """Report model readiness without exposing credential contents."""

        return self.llm_api_key is not None and bool(self.llm_api_key.get_secret_value())


@lru_cache
def get_settings() -> Settings:
    """Load and validate settings once per process."""

    return Settings()  # type: ignore[call-arg]
