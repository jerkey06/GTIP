import base64
from functools import lru_cache

from pydantic import field_validator, model_validator
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

    # URL pública del sitio (la del frontend). El proveedor OAuth redirige a
    # {PUBLIC_URL}/api/v1/auth/oauth/<proveedor>/callback, que el proxy envía a la API.
    public_url: str = "http://localhost:5173"
    # Inicio de sesión con Google y GitHub: cada proveedor se activa al definir sus dos valores.
    google_client_id: str | None = None
    google_client_secret: str | None = None
    github_client_id: str | None = None
    github_client_secret: str | None = None

    # Clerk (login con Google, GitHub o correo). La clave publicable es pública; de ella se
    # deduce el emisor de los tokens. CLERK_ISSUER permite fijarlo a mano (p. ej. dominio propio).
    clerk_publishable_key: str | None = None
    clerk_issuer: str | None = None

    cisa_kev_enabled: bool = True
    nvd_enabled: bool = True
    urlhaus_enabled: bool = True
    nvd_api_key: str | None = None
    # abuse.ch pide una Auth-Key gratuita para algunas descargas; opcional.
    urlhaus_auth_key: str | None = None
    abuseipdb_api_key: str | None = None
    otx_api_key: str | None = None

    # Consulta de datos sin iniciar sesión. La búsqueda y solicitar ingestas siguen exigiéndola.
    # Con PUBLIC_READ_ACCESS=false todo vuelve a requerir sesión.
    public_read_access: bool = True
    # Ejecuta el worker de ingesta dentro de la API (hosting sin proceso aparte, p. ej. Render
    # gratis). En producción con worker propio déjalo en false.
    embedded_worker: bool = False

    ingestion_poll_interval_seconds: int = 10
    ingestion_max_retries: int = 3
    # Frecuencias conservadoras por fuente, en minutos (ADD §8.4). 0 desactiva la planificación.
    cisa_kev_interval_minutes: int = 720
    nvd_interval_minutes: int = 120
    urlhaus_interval_minutes: int = 60
    # Primera sincronización de NVD: cuántos días hacia atrás (máximo 120 por petición).
    nvd_initial_days: int = 7
    # Una ejecución en running más tiempo que esto se considera abandonada (ADD §13.4).
    ingestion_stale_after_minutes: int = 60
    http_timeout_seconds: float = 30.0
    log_level: str = "INFO"

    # Carpeta con el frontend compilado para servirlo junto a la API (ADR-04). Opcional.
    frontend_dist_dir: str | None = None
    # Intentos de login permitidos por IP y minuto antes de responder 429.
    login_rate_limit_per_minute: int = 10

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_driver(cls, value: str) -> str:
        """Los proveedores (Render, Heroku…) entregan ``postgres://`` o ``postgresql://``."""
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix) :]
        return value

    @property
    def clerk_issuer_url(self) -> str | None:
        """URL del emisor (Frontend API de Clerk), o None si Clerk no está configurado."""
        if self.clerk_issuer:
            return self.clerk_issuer.rstrip("/")
        key = self.clerk_publishable_key
        if not key:
            return None
        try:
            encoded = key.split("_", 2)[2]
            domain = base64.b64decode(encoded + "=" * (-len(encoded) % 4)).decode().rstrip("$")
        except (IndexError, ValueError):
            raise ValueError("CLERK_PUBLISHABLE_KEY no tiene un formato válido.") from None
        return f"https://{domain}"

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
        if not 1 <= self.nvd_initial_days <= 120:
            raise ValueError("NVD_INITIAL_DAYS debe estar entre 1 y 120.")
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
