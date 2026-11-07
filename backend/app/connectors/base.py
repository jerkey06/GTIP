"""Interfaz común de los conectores (ADD §7.2) y cliente HTTP con reintentos (ADD §7.3).

Un conector descarga datos de una fuente y devuelve registros validados de
``app.domain.records``. Nunca escribe en la base de datos (ADD §6.4).
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.domain.records import ObservationRecord, VulnerabilityRecord

log = logging.getLogger("gtip.connectors")

USER_AGENT = "GTIP/0.1 (proyecto universitario de inteligencia de amenazas)"
MAX_RECORD_ERRORS_IN_SUMMARY = 5
# Errores transitorios que se reintentan (ADD §13.2). El resto de 4xx no.
RETRY_STATUS = {429, 500, 502, 503, 504}
MAX_RETRY_AFTER_SECONDS = 60.0

Sleep = Callable[[float], Awaitable[None]]


class ConnectorError(Exception):
    """La fuente no respondió o devolvió algo inutilizable. El mensaje no lleva secretos."""


@dataclass
class FetchResult:
    vulnerabilities: list[VulnerabilityRecord] = field(default_factory=list)
    observations: list[ObservationRecord] = field(default_factory=list)
    # Registros descartados por no superar la validación: la ejecución queda "partial".
    record_errors: list[str] = field(default_factory=list)
    # CVE del catálogo KEV completo, solo si se descargó entero (PRD §9.2).
    kev_catalog: set[str] | None = None

    @property
    def received(self) -> int:
        return len(self.vulnerabilities) + len(self.observations) + len(self.record_errors)

    def error_summary(self) -> str | None:
        if not self.record_errors:
            return None
        shown = self.record_errors[:MAX_RECORD_ERRORS_IN_SUMMARY]
        extra = len(self.record_errors) - len(shown)
        lines = [f"{len(self.record_errors)} registros descartados por datos inválidos:", *shown]
        if extra:
            lines.append(f"… y {extra} más")
        return "\n".join(lines)


class Connector(ABC):
    provider_key: ClassVar[str]

    def __init__(self, client: httpx.AsyncClient, settings: Settings, sleep: Sleep | None = None):
        self.client = client
        self.settings = settings
        self._sleep = sleep or asyncio.sleep

    @classmethod
    def unavailable_reason(cls, settings: Settings) -> str | None:
        """Motivo por el que la fuente no puede ejecutarse con esta configuración."""
        return None

    @abstractmethod
    async def fetch(self, since: datetime | None) -> FetchResult:
        """Descarga los datos nuevos o modificados desde ``since`` (o todos si es None)."""

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """GET con reintentos limitados para fallos transitorios (ADD §7.3 y §13.2)."""
        retries = self.settings.ingestion_max_retries
        for attempt in range(retries + 1):
            try:
                response = await self.client.get(url, params=params, headers=headers)
            except httpx.TransportError as exc:
                if attempt == retries:
                    raise ConnectorError(
                        f"No se pudo conectar con {self.provider_key}: {type(exc).__name__}"
                    ) from exc
                await self._backoff(attempt, None)
                continue

            if response.status_code in RETRY_STATUS and attempt < retries:
                await self._backoff(attempt, response.headers.get("Retry-After"))
                continue
            if response.is_error:
                # Sin la URL completa: podría llevar una clave en la consulta.
                raise ConnectorError(
                    f"{self.provider_key} respondió HTTP {response.status_code}"
                    f" ({response.reason_phrase})"
                )
            return response
        raise AssertionError("inalcanzable")

    async def _backoff(self, attempt: int, retry_after: str | None) -> None:
        delay = 2.0 * 2**attempt
        if retry_after:
            try:
                delay = min(float(retry_after), MAX_RETRY_AFTER_SECONDS)
            except ValueError:
                pass
        log.warning("Reintentando %s en %.1f s (intento %d)", self.provider_key, delay, attempt + 1)
        await self._sleep(delay)


def describe_error(exc: Exception) -> str:
    """Motivo breve por el que se descartó un registro."""
    if isinstance(exc, ValidationError):
        return "; ".join(e["msg"] for e in exc.errors())[:200]
    return f"{type(exc).__name__}: {exc}"[:200]


def json_body(response: httpx.Response, provider_key: str) -> Any:
    try:
        return response.json()
    except ValueError as exc:
        raise ConnectorError(f"{provider_key} devolvió una respuesta que no es JSON") from exc
