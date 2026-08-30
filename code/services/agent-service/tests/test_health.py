from fastapi.testclient import TestClient
from pydantic import SecretStr

from agent_service.config import Settings
from agent_service.database import DatabaseHealth
from agent_service.main import create_app


def test_health_returns_request_id_and_dependency_versions() -> None:
    settings = Settings(
        db_host="127.0.0.1",
        db_name="school_agent",
        db_username="school_agent",
        db_password=SecretStr("test-only"),
        core_url="http://127.0.0.1:8080",
    )
    app = create_app(
        settings=settings,
        database_probe=lambda _: DatabaseHealth("16.14", "0.8.3"),
    )

    with TestClient(app) as client:
        response = client.get("/health", headers={"X-Request-ID": "pytest-request"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "pytest-request"
    assert response.json()["requestId"] == "pytest-request"
    assert response.json()["data"]["database"]["version"] == ("PostgreSQL 16.14 / pgvector 0.8.3")
