"""Minimal PostgreSQL probe used by M01 readiness checks."""

from dataclasses import dataclass

import psycopg

from agent_service.config import Settings


@dataclass(frozen=True)
class DatabaseHealth:
    """Database versions returned without connection or credential details."""

    postgres_version: str
    vector_version: str


def probe_database(settings: Settings) -> DatabaseHealth:
    """Verify PostgreSQL and pgvector with a short-lived read-only connection."""

    with (
        psycopg.connect(
            host=settings.db_host,
            port=settings.db_port,
            dbname=settings.db_name,
            user=settings.db_username,
            password=settings.db_password.get_secret_value(),
            connect_timeout=3,
        ) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SELECT current_setting('server_version')")
        postgres_version = str(cursor.fetchone()[0])
        cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("pgvector extension is not installed")
        return DatabaseHealth(postgres_version, str(row[0]))
