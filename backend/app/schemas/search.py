from typing import Literal

from pydantic import BaseModel

from app.domain.enums import IndicatorType
from app.schemas.indicators import IndicatorRead
from app.schemas.vulnerabilities import VulnerabilityListItem


class ExactMatch(BaseModel):
    kind: Literal["vulnerability", "indicator"]
    cve_id: str | None = None
    indicator_id: int | None = None


class SearchGroup[T](BaseModel):
    items: list[T]
    total: int


class SearchResult(BaseModel):
    query: str
    # "cve", el tipo de indicador detectado o "text".
    kind: str
    indicator_type: IndicatorType | None
    exact_match: ExactMatch | None
    vulnerabilities: SearchGroup[VulnerabilityListItem]
    indicators: SearchGroup[IndicatorRead]
