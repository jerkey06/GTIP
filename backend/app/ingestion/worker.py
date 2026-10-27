"""Punto de entrada del worker de ingesta (proceso independiente de la API).

Por ahora solo mantiene el proceso vivo; el scheduler y la reclamación de
ingestion_jobs se implementan según el plan de semanas del ADD.
"""

import logging
import time

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    log = logging.getLogger("gtip.worker")
    log.info("Worker iniciado (env=%s)", settings.app_env)
    while True:
        time.sleep(settings.ingestion_poll_interval_seconds)


if __name__ == "__main__":
    main()
