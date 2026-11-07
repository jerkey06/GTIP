"""URLhaus (abuse.ch): URLs de distribución de malware añadidas recientemente.

abuse.ch retiró los volcados públicos (``/downloads/*`` responde 410) y ahora la API exige
una Auth-Key gratuita (https://auth.abuse.ch). Las URLs son datos potencialmente maliciosos:
solo se guardan como texto, nunca se visitan (ADD §12.4).
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from app.connectors.base import Connector, ConnectorError, FetchResult, describe_error
from app.core.config import Settings
from app.domain.enums import IndicatorType
from app.domain.indicators import InvalidIndicatorError
from app.domain.records import IndicatorRecord, ObservationRecord

API_URL = "https://urlhaus-api.abuse.ch/v1/urls/recent/limit/1000/"


def _datetime(value: str | None) -> datetime | None:
    value = (value or "").strip().removesuffix("UTC").strip()
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)


def parse_entry(entry: dict[str, Any]) -> ObservationRecord:
    added = _datetime(entry.get("date_added"))
    last_online = _datetime(entry.get("last_online"))
    last_seen = max((d for d in (added, last_online) if d), default=None)
    indicator = IndicatorRecord.from_value(
        IndicatorType.URL, entry["url"], first_seen_at=added, last_seen_at=last_seen
    )
    tags = [str(t).strip() for t in (entry.get("tags") or []) if str(t).strip()]
    external_id = str(entry.get("id") or "").strip() or None
    return ObservationRecord(
        indicator=indicator,
        external_id=external_id,
        first_seen_at=added,
        last_seen_at=last_seen,
        reference_url=(entry.get("urlhaus_reference") or "").strip() or None,
        source_data={
            "url_status": entry.get("url_status") or None,
            "threat": entry.get("threat") or None,
            "tags": tags,
            "reporter": entry.get("reporter") or None,
        },
    )


def parse_response(payload: Any) -> FetchResult:
    if not isinstance(payload, dict):
        raise ConnectorError("urlhaus devolvió una respuesta inesperada")
    status = payload.get("query_status")
    if status not in ("ok", "no_results"):
        raise ConnectorError(f"urlhaus respondió query_status={status!r}")
    result = FetchResult()
    for entry in payload.get("urls") or []:
        try:
            result.observations.append(parse_entry(entry))
        except (KeyError, TypeError, ValueError, InvalidIndicatorError, ValidationError) as exc:
            result.record_errors.append(f"id {entry.get('id') or '?'}: {describe_error(exc)}")
    return result


class UrlhausConnector(Connector):
    provider_key = "urlhaus"

    @classmethod
    def unavailable_reason(cls, settings: Settings) -> str | None:
        if not settings.urlhaus_enabled:
            return "Desactivada con URLHAUS_ENABLED=false"
        if not settings.urlhaus_auth_key:
            return "Falta URLHAUS_AUTH_KEY (clave gratuita en https://auth.abuse.ch)"
        return None

    async def fetch(self, since: datetime | None) -> FetchResult:
        response = await self.get(
            API_URL, headers={"Auth-Key": self.settings.urlhaus_auth_key or ""}
        )
        try:
            payload = response.json()
        except ValueError:
            raise ConnectorError("urlhaus no devolvió JSON válido") from None
        return parse_response(payload)
