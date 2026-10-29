from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_SECRET_KEYS = {"", "change-me"}


class Settings(BaseSettings):
    """Configuración central leída de variables de entorno o del archivo .env."""

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    app_env: str = "development"
    app_secret_key: str = "change-me"
    database_url: str = "postgresql+psycopg://gtip:gtip@localhost:5432/gtip"
    access_token_expire_minutes: int = 30
    jwt_algorithm: str = "HS256"

    cisa_kev_enabled: bool = True
    urlhaus_enabled: bool = True
    nvd_api_key: str | None = None
    abuseipdb_api_key: str | None = None
    otx_api_key: str | None = None

    ingestion_poll_interval_seconds: int = 10
    ingestion_max_retries: int = 3
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @model_validator(mode="after")
    def _validate_critical(self) -> "Settings":
        """Falla al arrancar con un mensaje claro si falta configuración crítica (ADD §18)."""
        if not self.database_url:
            raise ValueError("DATABASE_URL es obligatoria.")
        if self.access_token_expire_minutes <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES debe ser mayor que 0.")
        if self.is_production and (
            self.app_secret_key in INSECURE_SECRET_KEYS or len(self.app_secret_key) < 32
        ):
            raise ValueError(
                "APP_SECRET_KEY debe ser un valor aleatorio de al menos 32 caracteres en "
                "producción. Genera uno con: "
                'python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
