"""Logs estructurados en JSON para la API y el worker (ADD §15.1).

Nunca se registran contraseñas, tokens ni claves de API: el código no los pasa a
los logs y los mensajes de error de las fuentes se sanean antes de guardarse.
"""

import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def __init__(self, component: str) -> None:
        super().__init__()
        self.component = component

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "component": self.component,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


def configure_logging(level: str, component: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(component))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())
    # httpx registra cada URL, y la de NVD puede llevar parámetros sensibles.
    logging.getLogger("httpx").setLevel(logging.WARNING)
