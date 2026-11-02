from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import IndicatorType
from app.schemas.ingestions import IngestionRunRead
from app.schemas.sources import SourceRead
from app.schemas.vulnerabilities import VulnerabilityListItem


class CvssBucket(BaseModel):
    severity: str  # critical | high | medium | low | none | unscored
    label: str
    min_score: float | None
    count: int


class RecentIndicator(BaseModel):
    id: int
    indicator_type: IndicatorType
    value: str
    source_names: list[str]
    last_seen_at: datetime | None
    created_at: datetime


class DashboardStats(BaseModel):
    vulnerabilities_total: int
    vulnerabilities_kev: int
    indicators_total: int
    observations_recent: int
    observations_recent_days: int


class Dashboard(BaseModel):
    stats: DashboardStats
    sources: list[SourceRead]
    cvss_distribution: list[CvssBucket]
    latest_vulnerabilities: list[VulnerabilityListItem]
    recent_indicators: list[RecentIndicator]
    latest_runs: list[IngestionRunRead]
