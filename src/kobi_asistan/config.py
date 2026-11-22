"""Ayarları ortam değişkenlerinden (.env) okur.

Şifre ve API anahtarları koda yazılmaz; .env dosyasından gelir.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Ayarlar:
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int

    @property
    def veritabani_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


def ayarlari_yukle(env: dict[str, str] | None = None) -> Ayarlar:
    """Ayarları döndürür. Test için `env` sözlüğü verilebilir."""
    if env is None:
        load_dotenv()
        env = dict(os.environ)
    return Ayarlar(
        postgres_user=env.get("POSTGRES_USER", "kobi"),
        postgres_password=env.get("POSTGRES_PASSWORD", "kobi_sifre"),
        postgres_db=env.get("POSTGRES_DB", "kobi_asistan"),
        postgres_host=env.get("POSTGRES_HOST", "localhost"),
        postgres_port=int(env.get("POSTGRES_PORT", "5432")),
    )
