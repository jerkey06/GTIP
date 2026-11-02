from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.domain.enums import IngestionStatus, TriggerType
from app.models import IngestionRun, Source, User
from app.repositories._upsert import UpsertResult

MAX_ERROR_SUMMARY_LENGTH = 2000
ACTIVE_STATUSES = (IngestionStatus.PENDING, IngestionStatus.RUNNING)


class ActiveRunExistsError(Exception):
    """La fuente ya tiene una ejecución pendiente o en curso."""

    def __init__(self, active_run: IngestionRun | None) -> None:
        super().__init__("La fuente ya tiene una ingesta pendiente o en ejecución")
        self.active_run = active_run


def sanitize_error(message: str | None) -> str | None:
    """Recorta el mensaje y oculta las claves de API configuradas (ADD §8.3 y §15.1)."""
    if not message:
        return None
    settings = get_settings()
    for secret in (
        settings.nvd_api_key,
        settings.urlhaus_auth_key,
        settings.abuseipdb_api_key,
        settings.otx_api_key,
        settings.app_secret_key,
    ):
        if secret:
            message = message.replace(secret, "***")
    return message[:MAX_ERROR_SUMMARY_LENGTH]


def get_run(session: Session, run_id: int) -> IngestionRun | None:
    return session.get(
        IngestionRun,
        run_id,
        options=[joinedload(IngestionRun.source), joinedload(IngestionRun.requested_by)],
    )


def get_active_run(session: Session, source_id: int) -> IngestionRun | None:
    return session.scalar(
        select(IngestionRun).where(
            IngestionRun.source_id == source_id, IngestionRun.status.in_(ACTIVE_STATUSES)
        )
    )


def request_run(
    session: Session,
    source: Source,
    trigger_type: TriggerType,
    requested_by: User | None = None,
) -> IngestionRun:
    """Crea una solicitud ``pending`` para el worker (ADD §8.2). No hace commit.

    Lanza ``ActiveRunExistsError`` si la fuente ya tiene una pendiente o en curso; lo
    garantiza el índice único parcial ``uq_ingestion_runs_active_source``.
    """
    run = IngestionRun(
        source_id=source.id,
        status=IngestionStatus.PENDING,
        trigger_type=trigger_type,
        requested_by_id=requested_by.id if requested_by else None,
        requested_at=datetime.now(UTC),
    )
    try:
        with session.begin_nested():
            session.add(run)
    except IntegrityError:
        raise ActiveRunExistsError(get_active_run(session, source.id)) from None
    return run


def start_run(session: Session, source: Source, trigger_type: TriggerType) -> IngestionRun:
    """Crea la ejecución directamente en ``running`` y marca el intento. No hace commit."""
    now = datetime.now(UTC)
    run = IngestionRun(
        source_id=source.id,
        status=IngestionStatus.RUNNING,
        trigger_type=trigger_type,
        requested_at=now,
        claimed_at=now,
        started_at=now,
    )
    source.last_attempt_at = now
    session.add(run)
    session.flush()
    return run


def claim_next_pending(session: Session) -> IngestionRun | None:
    """Reclama la solicitud pendiente más antigua y la pasa a ``running``. No hace commit.

    ``FOR UPDATE SKIP LOCKED`` impide que dos workers reclamen la misma (ADD §6.5).
    """
    run = session.scalar(
        select(IngestionRun)
        .where(IngestionRun.status == IngestionStatus.PENDING)
        .order_by(IngestionRun.requested_at, IngestionRun.id)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    if run is None:
        return None
    now = datetime.now(UTC)
    run.status = IngestionStatus.RUNNING
    run.claimed_at = now
    run.started_at = now
    run.source.last_attempt_at = now
    session.flush()
    return run


def fail_stale_runs(session: Session, running_for: timedelta) -> list[IngestionRun]:
    """Marca como fallidas las ejecuciones que llevan demasiado en ``running`` (ADD §13.4).

    Ocurre si el worker se reinició a mitad de una ingesta. No hace commit.
    """
    limit = datetime.now(UTC) - running_for
    stale = list(
        session.scalars(
            select(IngestionRun)
            .where(
                IngestionRun.status == IngestionStatus.RUNNING,
                IngestionRun.started_at < limit,
            )
            .with_for_update(skip_locked=True)
        )
    )
    for run in stale:
        finish_run(
            session,
            run,
            IngestionStatus.FAILED,
            error_count=1,
            error_summary="La ejecución se interrumpió (el worker se detuvo o tardó demasiado).",
        )
    return stale


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


@dataclass(frozen=True)
class RunFilters:
    source_id: int | None = None
    status: IngestionStatus | None = None
    trigger_type: TriggerType | None = None
    requested_after: datetime | None = None
    requested_before: datetime | None = None


def _apply_filters(stmt: Select, f: RunFilters) -> Select:
    if f.source_id is not None:
        stmt = stmt.where(IngestionRun.source_id == f.source_id)
    if f.status is not None:
        stmt = stmt.where(IngestionRun.status == f.status)
    if f.trigger_type is not None:
        stmt = stmt.where(IngestionRun.trigger_type == f.trigger_type)
    if f.requested_after is not None:
        stmt = stmt.where(IngestionRun.requested_at >= f.requested_after)
    if f.requested_before is not None:
        stmt = stmt.where(IngestionRun.requested_at <= f.requested_before)
    return stmt


def list_runs(
    session: Session, filters: RunFilters, offset: int, limit: int
) -> tuple[list[IngestionRun], int]:
    """Historial, lo más reciente primero."""
    total = session.scalar(_apply_filters(select(func.count(IngestionRun.id)), filters)) or 0
    stmt = (
        _apply_filters(select(IngestionRun), filters)
        .options(joinedload(IngestionRun.source), joinedload(IngestionRun.requested_by))
        .order_by(IngestionRun.requested_at.desc(), IngestionRun.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.scalars(stmt)), total


def latest_run_by_source(session: Session) -> dict[int, IngestionRun]:
    """Última ejecución de cada fuente (para el estado de las fuentes, PRD §10.5)."""
    latest = (
        select(IngestionRun.source_id, func.max(IngestionRun.id).label("run_id"))
        .group_by(IngestionRun.source_id)
        .subquery()
    )
    runs = session.scalars(select(IngestionRun).join(latest, latest.c.run_id == IngestionRun.id))
    return {run.source_id: run for run in runs}
