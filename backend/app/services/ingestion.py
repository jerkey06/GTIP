"""Ejecución de una ingesta: conector → validación → upsert → resultado (ADD §8)."""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.connectors import ConnectorError, FetchResult, fetch_source
from app.core.config import Settings, get_settings
from app.domain.enums import IngestionStatus
from app.models import IngestionRun
from app.repositories import ingestion_runs
from app.repositories._upsert import UpsertResult
from app.repositories.indicators import upsert_observations
from app.repositories.vulnerabilities import (
    clear_known_exploited_except,
    upsert_vulnerabilities,
)

log = logging.getLogger("gtip.ingestion")

Fetcher = Callable[[str, datetime | None, Settings], Awaitable[FetchResult]]


def persist(session: Session, source_id: int, fetched: FetchResult) -> UpsertResult:
    """Guarda lo que devolvió un conector. No hace commit."""
    result = UpsertResult()
    if fetched.vulnerabilities:
        result += upsert_vulnerabilities(session, fetched.vulnerabilities)
    if fetched.kev_catalog is not None:
        cleared = clear_known_exploited_except(session, fetched.kev_catalog)
        result += UpsertResult(updated=cleared)
    if fetched.observations:
        result += upsert_observations(session, source_id, fetched.observations)
    return result


def execute_run(session: Session, run: IngestionRun, fetcher: Fetcher = fetch_source) -> None:
    """Ejecuta una ejecución ya reclamada (``running``) y la cierra con su resultado.

    Si la fuente falla, la ejecución queda ``failed`` y los datos anteriores se
    conservan (ADD §13.1). Hace commit al terminar.
    """
    settings = get_settings()
    source = run.source
    started = time.monotonic()
    log.info("Ingesta %s de %s iniciada", run.id, source.provider_key)

    try:
        fetched = asyncio.run(fetcher(source.provider_key, source.last_success_at, settings))
    except Exception as exc:  # cualquier fallo del conector deja la ejecución en failed
        message = str(exc) if isinstance(exc, ConnectorError) else f"{type(exc).__name__}: {exc}"
        log.warning("Ingesta %s de %s fallida: %s", run.id, source.provider_key, message)
        ingestion_runs.finish_run(
            session, run, IngestionStatus.FAILED, error_count=1, error_summary=message
        )
        session.commit()
        return

    try:
        result = persist(session, source.id, fetched)
        status = IngestionStatus.PARTIAL if fetched.record_errors else IngestionStatus.COMPLETED
        ingestion_runs.finish_run(
            session,
            run,
            status,
            result,
            error_count=len(fetched.record_errors),
            error_summary=fetched.error_summary(),
        )
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        log.exception("Error de base de datos en la ingesta %s", run.id)
        ingestion_runs.finish_run(
            session,
            run,
            IngestionStatus.FAILED,
            error_count=1,
            error_summary=f"Error al guardar en la base de datos: {type(exc).__name__}",
        )
        session.commit()
        return

    log.info(
        "Ingesta %s de %s: %s (%d procesados, %d nuevos, %d actualizados, %d errores) en %.1f s",
        run.id,
        source.provider_key,
        status,
        result.processed,
        result.created,
        result.updated,
        len(fetched.record_errors),
        time.monotonic() - started,
    )
