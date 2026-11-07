"""Registro de conectores por ``provider_key`` (los de la migración inicial)."""

from datetime import datetime

import httpx

from app.connectors.base import USER_AGENT, Connector, ConnectorError, FetchResult
from app.connectors.cisa_kev import CisaKevConnector
from app.connectors.nvd import NvdConnector
from app.connectors.urlhaus import UrlhausConnector
from app.core.config import Settings

CONNECTORS: dict[str, type[Connector]] = {
    c.provider_key: c for c in (CisaKevConnector, NvdConnector, UrlhausConnector)
}

# Fuentes opcionales del ADD §7.1 sin conector en el MVP, con la clave que necesitarían.
OPTIONAL_API_KEYS = {"abuseipdb": "ABUSEIPDB_API_KEY", "otx": "OTX_API_KEY"}


def unavailable_reason(provider_key: str, settings: Settings) -> str | None:
    """Por qué no se puede ingerir esta fuente, o ``None`` si se puede."""
    connector = CONNECTORS.get(provider_key)
    if connector is not None:
        return connector.unavailable_reason(settings)
    env = OPTIONAL_API_KEYS.get(provider_key)
    if env and not getattr(settings, env.lower()):
        return f"Falta {env}"
    return "Integración opcional pendiente: no tiene conector en el MVP"


async def fetch_source(
    provider_key: str, since: datetime | None, settings: Settings
) -> FetchResult:
    """Ejecuta el conector de una fuente con un cliente HTTP configurado (ADD §7.3)."""
    connector_cls = CONNECTORS.get(provider_key)
    if connector_cls is None:
        raise ConnectorError(f"No hay conector para la fuente {provider_key!r}")
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(settings.http_timeout_seconds),
        limits=httpx.Limits(max_connections=5),
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    ) as client:
        return await connector_cls(client, settings).fetch(since)


__all__ = [
    "CONNECTORS",
    "Connector",
    "ConnectorError",
    "FetchResult",
    "fetch_source",
    "unavailable_reason",
]
