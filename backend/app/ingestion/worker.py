"""Punto de entrada del worker de ingesta (proceso independiente de la API, ADR-02).

Uso, desde backend/:
    uv run python -m app.ingestion.worker            # bucle con planificador
    uv run python -m app.ingestion.worker --once     # procesa lo pendiente y termina

El bucle:
1. Marca como fallidas las ejecuciones abandonadas (ADD §13.4).
2. Reclama la solicitud pendiente más antigua y la ejecuta (ADD §8.2).
3. Si no hay nada pendiente, espera INGESTION_POLL_INTERVAL_SECONDS.
"""

import argparse
import logging
import signal
import threading
from datetime import timedelta

from sqlalchemy.exc import OperationalError

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import get_sessionmaker
from app.ingestion.scheduler import build_scheduler
from app.repositories import ingestion_runs
from app.services.ingestion import execute_run

log = logging.getLogger("gtip.worker")


def recover_stale_runs() -> int:
    settings = get_settings()
    with get_sessionmaker()() as session:
        stale = ingestion_runs.fail_stale_runs(
            session, timedelta(minutes=settings.ingestion_stale_after_minutes)
        )
        session.commit()
    for run in stale:
        log.warning("Ejecución %s marcada como fallida por abandono", run.id)
    return len(stale)


def process_next() -> bool:
    """Ejecuta una solicitud pendiente. Devuelve ``False`` si no había ninguna."""
    with get_sessionmaker()() as session:
        run = ingestion_runs.claim_next_pending(session)
        if run is None:
            session.rollback()
            return False
        session.commit()  # el historial ya muestra la ejecución en curso
        execute_run(session, run)
    return True


def run_pending(stop: threading.Event | None = None) -> int:
    processed = 0
    while not (stop and stop.is_set()) and process_next():
        processed += 1
    return processed


def run_forever(stop: threading.Event) -> None:
    """Bucle del worker: planificador periódico + atención de solicitudes pendientes."""
    settings = get_settings()
    scheduler = build_scheduler(settings)
    scheduler.start()
    try:
        while not stop.is_set():
            try:
                recover_stale_runs()
                run_pending(stop)
            except OperationalError:
                log.exception("No se pudo acceder a PostgreSQL; se reintentará")
            stop.wait(settings.ingestion_poll_interval_seconds)
    finally:
        scheduler.shutdown(wait=False)
        log.info("Worker detenido")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.ingestion.worker")
    parser.add_argument(
        "--once", action="store_true", help="Procesa las solicitudes pendientes y termina"
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    configure_logging(settings.log_level, component="worker")
    log.info("Worker iniciado (env=%s)", settings.app_env)

    if args.once:
        recover_stale_runs()
        log.info("Procesadas %d solicitudes", run_pending())
        return

    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())

    run_forever(stop)


if __name__ == "__main__":
    main()
