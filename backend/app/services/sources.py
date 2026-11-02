"""Estado de las fuentes a partir de sus ejecuciones y de la configuración (PRD §10.5)."""

from sqlalchemy.orm import Session

from app.connectors import CONNECTORS, OPTIONAL_API_KEYS, unavailable_reason
from app.core.config import Settings
from app.ingestion.scheduler import interval_minutes
from app.models import IngestionRun, Source
from app.repositories import ingestion_runs
from app.repositories import sources as sources_repo
from app.schemas.sources import LastRunSummary, SourceRead

# Fuentes cuya clave es opcional pero mejora los límites de uso.
_OPTIONAL_KEYS = {"nvd": "nvd_api_key", "urlhaus": "urlhaus_auth_key"}


def disabled_reason(source: Source, settings: Settings) -> str | None:
    if not source.is_enabled:
        reason = unavailable_reason(source.provider_key, settings)
        return reason or "Deshabilitada en la base de datos"
    return unavailable_reason(source.provider_key, settings)


def _api_key_configured(provider_key: str, settings: Settings) -> bool | None:
    if provider_key in OPTIONAL_API_KEYS:
        return bool(getattr(settings, OPTIONAL_API_KEYS[provider_key].lower()))
    if provider_key in _OPTIONAL_KEYS:
        return bool(getattr(settings, _OPTIONAL_KEYS[provider_key]))
    return None


def to_read(
    source: Source,
    settings: Settings,
    last_run: IngestionRun | None,
) -> SourceRead:
    reason = disabled_reason(source, settings)
    minutes = interval_minutes(source.provider_key, settings)
    active = last_run if last_run and not last_run.status.is_final else None
    return SourceRead(
        id=source.id,
        provider_key=source.provider_key,
        name=source.name,
        description=source.description,
        base_url=source.base_url,
        is_enabled=reason is None,
        disabled_reason=reason,
        requires_api_key=source.provider_key in OPTIONAL_API_KEYS,
        api_key_configured=_api_key_configured(source.provider_key, settings),
        schedule_interval_minutes=(
            minutes if minutes > 0 and source.provider_key in CONNECTORS else None
        ),
        last_attempt_at=source.last_attempt_at,
        last_success_at=source.last_success_at,
        last_error=source.last_error,
        last_run=(
            LastRunSummary(
                id=last_run.id,
                status=last_run.status,
                requested_at=last_run.requested_at,
                finished_at=last_run.finished_at,
                records_processed=last_run.records_processed,
                records_created=last_run.records_created,
                records_updated=last_run.records_updated,
                error_count=last_run.error_count,
            )
            if last_run
            else None
        ),
        active_run_id=active.id if active else None,
    )


def list_source_reads(session: Session, settings: Settings) -> list[SourceRead]:
    latest = ingestion_runs.latest_run_by_source(session)
    return [to_read(s, settings, latest.get(s.id)) for s in sources_repo.list_sources(session)]


def get_source_read(session: Session, settings: Settings, source_id: int) -> SourceRead | None:
    source = sources_repo.get_by_id(session, source_id)
    if source is None:
        return None
    latest = ingestion_runs.latest_run_by_source(session).get(source.id)
    return to_read(source, settings, latest)
