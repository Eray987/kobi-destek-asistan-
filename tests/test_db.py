"""Tests that need a real database. Start it first: docker compose up -d"""

import pytest

from kobi_asistan.db import connect, pgvector_version

pytestmark = pytest.mark.db


def test_pgvector_is_installed():
    with connect() as conn:
        assert pgvector_version(conn) is not None


def test_nearest_vector_comes_first():
    """Tries pgvector's nearest-neighbour search on a tiny example."""
    with connect() as conn:
        conn.execute("CREATE TEMP TABLE chunk (id text, emb vector(3))")
        conn.execute(
            "INSERT INTO chunk VALUES "
            "('returns', '[1,0,0]'), ('shipping', '[0,1,0]'), ('warranty', '[0,0,1]')"
        )
        nearest = conn.execute(
            "SELECT id FROM chunk ORDER BY emb <=> '[0.9,0.1,0]' LIMIT 1"
        ).fetchone()[0]
    assert nearest == "returns"
