"""Estadísticas del dashboard, siempre calculadas a partir de los datos guardados (ADD §15.3)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import Indicator, Observation, Source, Vulnerability
from app.repositories import ingestion_runs
from app.repositories.ingestion_runs import RunFilters
from app.schemas.dashboard import (
    CvssBucket,
    Dashboard,
    DashboardStats,
    RecentIndicator,
)
from app.schemas.ingestions import IngestionRunRead
from app.schemas.vulnerabilities import VulnerabilityListItem
from app.services.sources import list_source_reads

RECENT_DAYS = 7
LATEST_ROWS = 5

# Rangos estándar de CVSS v3 (UI §4.8). El orden es el de la gráfica.
CVSS_BUCKETS = (
    ("critical", "Crítica", 9.0, 10.0),
    ("high", "Alta", 7.0, 8.9),
    ("medium", "Media", 4.0, 6.9),
    ("low", "Baja", 0.1, 3.9),
    ("none", "Ninguna", 0.0, 0.0),
)


def _cvss_distribution(session: Session) -> list[CvssBucket]:
    score = Vulnerability.cvss_score
    columns = [
        func.count().filter(score.between(low, high)).label(key)
        for key, _, low, high in CVSS_BUCKETS
    ]
    columns.append(func.count().filter(score.is_(None)).label("unscored"))
    row = session.execute(select(*columns)).one()
    buckets = [
        CvssBucket(severity=key, label=label, min_score=low, count=row._mapping[key])
        for key, label, low, _ in CVSS_BUCKETS
    ]
    buckets.append(
        CvssBucket(severity="unscored", label="Sin puntuación", min_score=None, count=row.unscored)
    )
    return buckets


def _recent_indicators(session: Session) -> list[RecentIndicator]:
    indicators = list(
        session.scalars(
            select(Indicator)
            .order_by(Indicator.created_at.desc(), Indicator.id.desc())
            .limit(LATEST_ROWS)
        )
    )
    if not indicators:
        return []
    rows = session.execute(
        select(Observation.indicator_id, Source.name)
        .join(Source, Source.id == Observation.source_id)
        .where(Observation.indicator_id.in_([i.id for i in indicators]))
        .distinct()
        .order_by(Source.name)
    ).all()
    names: dict[int, list[str]] = {}
    for indicator_id, name in rows:
        names.setdefault(indicator_id, []).append(name)
    return [
        RecentIndicator(
            id=i.id,
            indicator_type=i.indicator_type,
            value=i.value,
            source_names=names.get(i.id, []),
            last_seen_at=i.last_seen_at,
            created_at=i.created_at,
        )
        for i in indicators
    ]


def build_dashboard(session: Session, settings: Settings) -> Dashboard:
    since = datetime.now(UTC) - timedelta(days=RECENT_DAYS)
    vuln_total, vuln_kev = session.execute(
        select(
            func.count(Vulnerability.id),
            func.coalesce(
                func.sum(case((Vulnerability.is_known_exploited.is_(True), 1), else_=0)), 0
            ),
        )
    ).one()
    stats = DashboardStats(
        vulnerabilities_total=vuln_total,
        vulnerabilities_kev=vuln_kev,
        indicators_total=session.scalar(select(func.count(Indicator.id))) or 0,
        observations_recent=session.scalar(
            select(func.count(Observation.id)).where(Observation.observed_at >= since)
        )
        or 0,
        observations_recent_days=RECENT_DAYS,
    )
    latest_vulns = session.scalars(
        select(Vulnerability)
        .order_by(Vulnerability.created_at.desc(), Vulnerability.id.desc())
        .limit(LATEST_ROWS)
    )
    runs, _ = ingestion_runs.list_runs(session, RunFilters(), 0, LATEST_ROWS)
    return Dashboard(
        stats=stats,
        sources=list_source_reads(session, settings),
        cvss_distribution=_cvss_distribution(session),
        latest_vulnerabilities=[VulnerabilityListItem.model_validate(v) for v in latest_vulns],
        recent_indicators=_recent_indicators(session),
        latest_runs=[IngestionRunRead.model_validate(r) for r in runs],
    )
