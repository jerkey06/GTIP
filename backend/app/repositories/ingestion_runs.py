from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.enums import IngestionStatus, TriggerType
from app.models import IngestionRun, Source
from app.repositories._upsert import UpsertResult

MAX_ERROR_SUMMARY_LENGTH = 2000


def sanitize_error(message: str | None) -> str | None:
    """Recorta el mensaje y oculta las claves de API configuradas (ADD §8.3 y §15.1)."""
    if not message:
        return None
    settings = get_settings()
    for secret in (
        settings.nvd_api_key,
        settings.abuseipdb_api_key,
        settings.otx_api_key,
        settings.app_secret_key,
    ):
        if secret:
            message = message.replace(secret, "***")
    return message[:MAX_ERROR_SUMMARY_LENGTH]


def get_run(session: Session, run_id: int) -> IngestionRun | None:
    return session.get(IngestionRun, run_id)


def start_run(session: Session, source: Source, trigger_type: TriggerType) -> IngestionRun:
    """Crea la ejecución en estado ``running`` y marca el intento en la fuente. No hace commit."""
    now = datetime.now(UTC)
    run = IngestionRun(
        source_id=source.id,
        status=IngestionStatus.RUNNING,
        trigger_type=trigger_type,
        started_at=now,
    )
    source.last_attempt_at = now
    session.add(run)
    session.flush()
    return run


def finish_run(
    session: Session,
    run: IngestionRun,
    status: IngestionStatus,
    result: UpsertResult | None = None,
    *,
    error_count: int = 0,
    error_summary: str | None = None,
) -> IngestionRun:
    """Cierra la ejecución con su resultado y actualiza el estado técnico de la fuente.

    Un fallo no toca los datos guardados antes: solo se registra (ADD §13.1). No hace commit.
    """
    if not status.is_final:
        raise ValueError(f"Estado final inválido para una ejecución: {status}")

    now = datetime.now(UTC)
    result = result or UpsertResult()
    run.status = status
    run.finished_at = now
    run.records_processed = result.processed
    run.records_created = result.created
    run.records_updated = result.updated
    run.error_count = error_count
    run.error_summary = sanitize_error(error_summary)

    source = run.source
    if status is IngestionStatus.FAILED:
        source.last_error = run.error_summary
    else:
        source.last_success_at = now
        source.last_error = run.error_summary if status is IngestionStatus.PARTIAL else None
    session.flush()
    return run
