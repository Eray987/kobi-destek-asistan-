"""Database connection helpers."""

import psycopg

from kobi_asistan.config import Settings, load_settings


def connect(settings: Settings | None = None) -> psycopg.Connection:
    settings = settings or load_settings()
    return psycopg.connect(settings.database_url, connect_timeout=3)


def pgvector_version(conn: psycopg.Connection) -> str | None:
    """Returns the installed pgvector version, or None if the extension is missing."""
    row = conn.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'").fetchone()
    return row[0] if row else None
