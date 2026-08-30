import pytest
from pydantic import ValidationError

from agent_service.config import Settings


def test_required_database_configuration_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "SCHOOL_AGENT_DB_HOST",
        "SCHOOL_AGENT_DB_NAME",
        "SCHOOL_AGENT_DB_USERNAME",
        "SCHOOL_AGENT_DB_PASSWORD",
        "SCHOOL_AGENT_CORE_URL",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]
