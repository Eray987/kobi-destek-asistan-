import os

import pytest

from kobi_asistan.db import connect


def _db_available() -> bool:
    try:
        with connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    """Skip `db` tests instead of failing when no database is running locally."""
    # In CI the database must always be there; skipping would hide failures.
    if os.environ.get("CI_REQUIRE_DB") or _db_available():
        return
    skip = pytest.mark.skip(reason="Database is not running (docker compose up -d)")
    for item in items:
        if "db" in item.keywords:
            item.add_marker(skip)
