"""Planificación periódica de ingestas con APScheduler (ADR-06).

El planificador no ejecuta conectores: solo crea solicitudes ``pending`` con
``trigger_type=scheduled``. Las ejecuta el mismo bucle que atiende las manuales.
"""

import logging
from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.connectors import CONNECTORS, unavailable_reason
from app.core.config import Settings
from app.db.session import get_sessionmaker
from app.domain.enums import TriggerType
from app.repositories import ingestion_runs, sources

log = logging.getLogger("gtip.scheduler")


def interval_minutes(provider_key: str, settings: Settings) -> int:
    """Frecuencia configurada de una fuente en minutos; 0 si no se planifica."""
    return int(getattr(settings, f"{provider_key}_interval_minutes", 0) or 0)


def enqueue_scheduled(provider_key: str, settings: Settings) -> None:
    """Pide una ingesta programada si la fuente está habilitada y no tiene otra activa."""
    with get_sessionmaker()() as session:
        source = sources.get_by_provider_key(session, provider_key)
        if source is None or not source.is_enabled or unavailable_reason(provider_key, settings):
            return
        try:
            run = ingestion_runs.request_run(session, source, TriggerType.SCHEDULED)
        except ingestion_runs.ActiveRunExistsError:
            log.info("%s ya tiene una ingesta activa; se omite la programada", provider_key)
            return
        session.commit()
        log.info("Ingesta programada %s de %s solicitada", run.id, provider_key)


def build_scheduler(settings: Settings) -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=UTC)
    with get_sessionmaker()() as session:
        last_success = {s.provider_key: s.last_success_at for s in sources.list_sources(session)}

    now = datetime.now(UTC)
    for provider_key in CONNECTORS:
        minutes = interval_minutes(provider_key, settings)
        if minutes <= 0:
            continue
        interval = timedelta(minutes=minutes)
        # La primera vez se sincroniza enseguida; después se respeta el intervalo aunque
        # el worker se reinicie.
        previous = last_success.get(provider_key)
        first_run = max(previous + interval, now) if previous else now + timedelta(seconds=5)
        scheduler.add_job(
            enqueue_scheduled,
            IntervalTrigger(minutes=minutes, start_date=first_run, timezone=UTC),
            args=[provider_key, settings],
            id=f"ingest-{provider_key}",
            next_run_time=first_run,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=None,
        )
        log.info("Ingesta de %s cada %d min; próxima: %s", provider_key, minutes, first_run)
    return scheduler
