"""Valores válidos del dominio. No dependen de SQLAlchemy ni de FastAPI (ADD §5.1)."""

from enum import StrEnum


class IndicatorType(StrEnum):
    """Tipos de IOC admitidos en el MVP (PRD §9.3)."""

    IPV4 = "ipv4"
    IPV6 = "ipv6"
    DOMAIN = "domain"
    URL = "url"
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"


class IngestionStatus(StrEnum):
    """Estados de una ejecución o solicitud de ingesta (ADD §8.3)."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"

    @property
    def is_final(self) -> bool:
        return self in {IngestionStatus.COMPLETED, IngestionStatus.PARTIAL, IngestionStatus.FAILED}


class TriggerType(StrEnum):
    """Origen de una ejecución de ingesta."""

    MANUAL = "manual"
    SCHEDULED = "scheduled"
