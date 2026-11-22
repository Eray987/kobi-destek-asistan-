import os

import pytest

from kobi_asistan.db import baglan


def _db_erisilebilir() -> bool:
    try:
        with baglan() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    """Veritabanı çalışmıyorsa `db` testlerini hata vermek yerine atla."""
    # CI'da veritabanı her zaman olmalı; orada atlamak hatayı gizler.
    if os.environ.get("CI_DB_ZORUNLU") or _db_erisilebilir():
        return
    atla = pytest.mark.skip(reason="Veritabanı çalışmıyor (docker compose up -d)")
    for item in items:
        if "db" in item.keywords:
            item.add_marker(atla)
