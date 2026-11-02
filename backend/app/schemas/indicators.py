from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.domain.enums import IndicatorType
from app.repositories.indicators import IndicatorSummary
from app.schemas.common import Page, SourceRef


class IndicatorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    indicator_type: IndicatorType
    value: str
    normalized_value: str
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    created_at: datetime
    source_count: int
    observation_count: int

    @classmethod
    def from_summary(cls, summary: IndicatorSummary) -> "IndicatorRead":
        i = summary.indicator
        return cls(
            id=i.id,
            indicator_type=i.indicator_type,
            value=i.value,
            normalized_value=i.normalized_value,
            first_seen_at=i.first_seen_at,
            last_seen_at=i.last_seen_at,
            created_at=i.created_at,
            source_count=summary.source_count,
            observation_count=summary.observation_count,
        )


class IndicatorSearchPage(Page[IndicatorRead]):
    # Tipo detectado o elegido para el valor buscado; None si no se buscó un valor.
    detected_type: IndicatorType | None = None
    # True si se buscó por coincidencia exacta del valor normalizado.
    exact: bool = False


class ObservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: SourceRef
    external_id: str | None
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    observed_at: datetime
    reference_url: str | None
    source_data: dict[str, Any]
