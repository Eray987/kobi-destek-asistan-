"""Gerçek veritabanı gerektiren testler. Çalıştırmadan önce: docker compose up -d"""

import pytest

from kobi_asistan.db import baglan, pgvector_surumu

pytestmark = pytest.mark.db


def test_pgvector_kurulu():
    with baglan() as conn:
        assert pgvector_surumu(conn) is not None


def test_benzer_vektor_once_gelir():
    """pgvector'ün en yakın komşu aramasını küçük bir örnekle dener."""
    with baglan() as conn:
        conn.execute("CREATE TEMP TABLE parca (id text, emb vector(3))")
        conn.execute(
            "INSERT INTO parca VALUES "
            "('iade', '[1,0,0]'), ('kargo', '[0,1,0]'), ('garanti', '[0,0,1]')"
        )
        en_yakin = conn.execute(
            "SELECT id FROM parca ORDER BY emb <=> '[0.9,0.1,0]' LIMIT 1"
        ).fetchone()[0]
    assert en_yakin == "iade"
