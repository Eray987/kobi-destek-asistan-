"""Loads settings from environment variables (.env).

Passwords and API keys never live in the code; they come from the .env file.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


def load_settings(env: dict[str, str] | None = None) -> Settings:
    """Returns the settings. Pass `env` to override the environment in tests."""
    if env is None:
        load_dotenv()
        env = dict(os.environ)
    return Settings(
        postgres_user=env.get("POSTGRES_USER", "kobi"),
        postgres_password=env.get("POSTGRES_PASSWORD", "kobi_password"),
        postgres_db=env.get("POSTGRES_DB", "kobi_asistan"),
        postgres_host=env.get("POSTGRES_HOST", "localhost"),
        postgres_port=int(env.get("POSTGRES_PORT", "5432")),
    )
