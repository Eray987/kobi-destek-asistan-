"""Veritabanı bağlantısı."""

import psycopg

from kobi_asistan.config import Ayarlar, ayarlari_yukle


def baglan(ayarlar: Ayarlar | None = None) -> psycopg.Connection:
    ayarlar = ayarlar or ayarlari_yukle()
    return psycopg.connect(ayarlar.veritabani_url, connect_timeout=3)


def pgvector_surumu(conn: psycopg.Connection) -> str | None:
    """pgvector eklentisi kuruluysa sürümünü, değilse None döndürür."""
    satir = conn.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'").fetchone()
    return satir[0] if satir else None
