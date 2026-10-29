"""Registros normalizados que los conectores entregan al núcleo para persistirlos.

Es el contrato entre conectores (área B) y repositorios (área A): un conector nunca
escribe en tablas, devuelve estos modelos validados y el repositorio hace el upsert
(ADD §6.4 y §9.2).

Un campo en ``None`` significa "la fuente no aporta este dato": el upsert conserva
el valor que ya estuviera guardado en lugar de borrarlo. Así CISA KEV y NVD pueden
actualizar la misma vulnerabilidad sin pisarse.
"""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import IndicatorType

CVE_ID_PATTERN = re.compile(r"^CVE-\d{4}-\d{4,}$")


class VulnerabilityRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    cve_id: str
    description: str | None = None
    cvss_score: Decimal | None = Field(default=None, ge=0, le=10)
    cvss_version: str | None = Field(default=None, max_length=10)
    cvss_vector: str | None = None
    published_at: datetime | None = None
    modified_at: datetime | None = None
    # None = la fuente no dice nada sobre KEV; False solo desde una sincronización completa
    # del catálogo (PRD §9.2).
    is_known_exploited: bool | None = None
    kev_added_at: date | None = None

    @field_validator("cve_id")
    @classmethod
    def _normalize_cve_id(cls, value: str) -> str:
        value = value.strip().upper()
        if not CVE_ID_PATTERN.match(value):
            raise ValueError(f"Identificador CVE inválido: {value!r}")
        return value


class IndicatorRecord(BaseModel):
    """Identidad de un IOC. ``normalized_value`` ya viene normalizado por el conector."""

    model_config = ConfigDict(frozen=True)

    indicator_type: IndicatorType
    value: str = Field(min_length=1)
    normalized_value: str = Field(min_length=1)
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None


class ObservationRecord(BaseModel):
    """Evidencia de una fuente sobre un indicador, con su procedencia (ADD §9.3)."""

    model_config = ConfigDict(frozen=True)

    indicator: IndicatorRecord
    external_id: str | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    reference_url: str | None = None
    source_data: dict[str, Any] = Field(default_factory=dict)
