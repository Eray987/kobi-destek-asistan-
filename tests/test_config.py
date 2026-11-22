from kobi_asistan.config import load_settings


def test_default_settings():
    settings = load_settings(env={})
    assert settings.postgres_host == "localhost"
    assert settings.postgres_port == 5432


def test_database_url_is_built_from_environment():
    settings = load_settings(
        env={
            "POSTGRES_USER": "u",
            "POSTGRES_PASSWORD": "p",
            "POSTGRES_DB": "d",
            "POSTGRES_HOST": "h",
            "POSTGRES_PORT": "6543",
        }
    )
    assert settings.database_url == "postgresql://u:p@h:6543/d"
