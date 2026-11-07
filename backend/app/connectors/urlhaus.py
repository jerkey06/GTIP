"""URLhaus (abuse.ch): URLs de distribución de malware añadidas en los últimos 30 días.

Se usa el volcado CSV público ``csv_recent``. Las URLs son datos potencialmente
maliciosos: solo se guardan como texto, nunca se visitan (ADD §12.4).
"""

import csv
import io
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from app.connectors.base import Connector, ConnectorError, FetchResult, describe_error
from app.core.config import Settings
from app.domain.enums import IndicatorType
from app.domain.indicators import InvalidIndicatorError
from app.domain.records import IndicatorRecord, ObservationRecord

CSV_URL = "https://urlhaus.abuse.ch/downloads/csv_recent/"
COLUMNS = [
    "id",
    "dateadded",
    "url",
    "url_status",
    "last_online",
    "threat",
    "tags",
    "urlhaus_link",
    "reporter",
]


def _datetime(value: str | None) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)


def parse_row(row: dict[str, Any]) -> ObservationRecord:
    added = _datetime(row.get("dateadded"))
    last_online = _datetime(row.get("last_online"))
    last_seen = max((d for d in (added, last_online) if d), default=None)
    indicator = IndicatorRecord.from_value(
        IndicatorType.URL, row["url"], first_seen_at=added, last_seen_at=last_seen
    )
    tags = [t.strip() for t in (row.get("tags") or "").split(",") if t.strip()]
    return ObservationRecord(
        indicator=indicator,
        external_id=(row.get("id") or "").strip() or None,
        first_seen_at=added,
        last_seen_at=last_seen,
        reference_url=(row.get("urlhaus_link") or "").strip() or None,
        source_data={
            "url_status": row.get("url_status") or None,
            "threat": row.get("threat") or None,
            "tags": tags,
            "reporter": row.get("reporter") or None,
        },
    )


def parse_csv(text: str) -> FetchResult:
    lines = [line for line in text.splitlines() if line.strip() and not line.startswith("#")]
    result = FetchResult()
    for row in csv.DictReader(io.StringIO("\n".join(lines)), fieldnames=COLUMNS):
        try:
            result.observations.append(parse_row(row))
        except (KeyError, TypeError, ValueError, InvalidIndicatorError, ValidationError) as exc:
            result.record_errors.append(f"id {row.get('id') or '?'}: {describe_error(exc)}")
    return result


class UrlhausConnector(Connector):
    provider_key = "urlhaus"

    @classmethod
    def unavailable_reason(cls, settings: Settings) -> str | None:
        if not settings.urlhaus_enabled:
            return "Desactivada con URLHAUS_ENABLED=false"
        return None

    async def fetch(self, since: datetime | None) -> FetchResult:
        headers = (
            {"Auth-Key": self.settings.urlhaus_auth_key} if self.settings.urlhaus_auth_key else None
        )
        response = await self.get(CSV_URL, headers=headers)
        if "<html" in response.text[:500].lower():
            raise ConnectorError("urlhaus devolvió HTML en lugar del CSV esperado")
        return parse_csv(response.text)
