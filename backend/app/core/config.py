from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración central leída de variables de entorno o del archivo .env."""

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    app_env: str = "development"
    app_secret_key: str = "change-me"
    database_url: str = "postgresql+psycopg://gtip:gtip@localhost:5432/gtip"
    access_token_expire_minutes: int = 30

    cisa_kev_enabled: bool = True
    urlhaus_enabled: bool = True
    nvd_api_key: str | None = None
    abuseipdb_api_key: str | None = None
    otx_api_key: str | None = None

    ingestion_poll_interval_seconds: int = 10
    ingestion_max_retries: int = 3
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
