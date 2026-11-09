from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from app.connectors.base import Connector, ConnectorError, FetchResult, describe_error
from app.core.config import Settings
from app.domain.enums import IndicatorType
from app.domain.indicators import InvalidIndicatorError
from app.domain.records import IndicatorRecord, ObservationRecord

API_URL = "https://api.abuseipdb.com/api/v2/blacklist"


def parse_entry(entry: dict[str, Any]) -> ObservationRecord:
    ip_address = str(entry.get("ipAddress") or "").strip()
    indicator = IndicatorRecord.from_value(IndicatorType.IP, ip_address)
    
    return ObservationRecord(
        indicator=indicator,
        external_id=ip_address,
        source_data={
            "abuse_confidence_score": entry.get("abuseConfidenceScore"),
            "country_code": entry.get("countryCode"),
            "total_reports": entry.get("totalReports"),
            "last_reported_at": entry.get("lastReportedAt"),
        },
    )


def parse_response(payload: Any) -> FetchResult:
    if not isinstance(payload, dict):
        raise ConnectorError("abuseipdb devolvió una respuesta inesperada")
    
    data = payload.get("data")
    if not isinstance(data, list):
        raise ConnectorError("abuseipdb: la respuesta no contiene la lista 'data'")

    result = FetchResult()
    for entry in data:
        try:
            result.observations.append(parse_entry(entry))
        except (KeyError, TypeError, ValueError, InvalidIndicatorError, ValidationError) as exc:
            result.record_errors.append(f"ip {entry.get('ipAddress') or '?'}: {describe_error(exc)}")
    return result


class AbuseIpDbConnector(Connector):
    provider_key = "abuseipdb"

    @classmethod
    def unavailable_reason(cls, settings: Settings) -> str | None:
        if not settings.abuseipdb_enabled:
            return "Desactivada con ABUSEIPDB_ENABLED=false"
        if not settings.abuseipdb_api_key:
            return "Falta ABUSEIPDB_API_KEY"
        return None

    async def fetch(self, since: datetime | None) -> FetchResult:
        response = await self.get(
            API_URL,
            params={"confidenceMinimum": "90", "limit": "10000"},
            headers={
                "Key": self.settings.abuseipdb_api_key or "",
                "Accept": "application/json",
            },
        )
        try:
            payload = response.json()
        except ValueError:
            raise ConnectorError("abuseipdb no devolvió JSON válido") from None
        return parse_response(payload)
