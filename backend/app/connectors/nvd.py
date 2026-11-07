"""NVD CVE API 2.0: CVE modificadas en un intervalo, con paginación y límite de frecuencia.

Límites públicos: 5 peticiones cada 30 s sin clave y 50 con clave; el intervalo de
fechas de una consulta no puede superar 120 días.
https://nvd.nist.gov/developers/vulnerabilities
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from pydantic import ValidationError

from app.connectors.base import (
    Connector,
    ConnectorError,
    FetchResult,
    describe_error,
    json_body,
)
from app.core.config import Settings
from app.domain.records import VulnerabilityRecord

API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
RESULTS_PER_PAGE = 2000
MAX_RANGE = timedelta(days=120)
# Margen para no perder CVE modificadas mientras terminaba la ejecución anterior.
OVERLAP = timedelta(minutes=15)
DELAY_WITHOUT_KEY = 6.0
DELAY_WITH_KEY = 0.6
MAX_REFERENCES = 50
# Preferencia de métricas: CVSS v3.1, v3.0, v4.0 y, como último recurso, v2.
METRIC_KEYS = ("cvssMetricV31", "cvssMetricV30", "cvssMetricV40", "cvssMetricV2")


def _datetime(value: Any) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value))
    # NVD devuelve las fechas en UTC sin zona horaria.
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _metric(metrics: dict[str, Any]) -> dict[str, Any] | None:
    for key in METRIC_KEYS:
        entries = metrics.get(key) or []
        if entries:
            primary = next((m for m in entries if m.get("type") == "Primary"), entries[0])
            return primary.get("cvssData") or None
    return None


def parse_cve(cve: dict[str, Any]) -> VulnerabilityRecord:
    descriptions = cve.get("descriptions") or []
    description = next(
        (d.get("value") for d in descriptions if d.get("lang") == "en"),
        descriptions[0].get("value") if descriptions else None,
    )
    metric = _metric(cve.get("metrics") or {})
    references = [
        {"url": r["url"], "source": r.get("source"), "tags": r.get("tags") or []}
        for r in (cve.get("references") or [])[:MAX_REFERENCES]
        if r.get("url")
    ]
    return VulnerabilityRecord(
        cve_id=cve["id"],
        description=(description or "").strip() or None,
        cvss_score=Decimal(str(metric["baseScore"])) if metric else None,
        cvss_version=metric.get("version") if metric else None,
        cvss_vector=metric.get("vectorString") if metric else None,
        published_at=_datetime(cve.get("published")),
        modified_at=_datetime(cve.get("lastModified")),
        nvd_references=references or None,
    )


class NvdConnector(Connector):
    provider_key = "nvd"

    @classmethod
    def unavailable_reason(cls, settings: Settings) -> str | None:
        if not settings.nvd_enabled:
            return "Desactivada con NVD_ENABLED=false"
        return None

    def window(self, since: datetime | None, now: datetime) -> tuple[datetime, datetime]:
        if since is None:
            start = now - timedelta(days=self.settings.nvd_initial_days)
        else:
            start = since - OVERLAP
        # Si la última sincronización es muy antigua se recuperan los últimos 120 días.
        return max(start, now - MAX_RANGE), now

    async def fetch(self, since: datetime | None) -> FetchResult:
        start, end = self.window(since, datetime.now(UTC))
        headers = {"apiKey": self.settings.nvd_api_key} if self.settings.nvd_api_key else None
        delay = DELAY_WITH_KEY if self.settings.nvd_api_key else DELAY_WITHOUT_KEY

        result = FetchResult()
        start_index = 0
        while True:
            params = {
                "lastModStartDate": start.isoformat(timespec="milliseconds"),
                "lastModEndDate": end.isoformat(timespec="milliseconds"),
                "resultsPerPage": RESULTS_PER_PAGE,
                "startIndex": start_index,
            }
            data = json_body(await self.get(API_URL, params=params, headers=headers), "nvd")
            if not isinstance(data, dict) or not isinstance(data.get("vulnerabilities"), list):
                raise ConnectorError("nvd: la respuesta no contiene la lista 'vulnerabilities'")

            for item in data["vulnerabilities"]:
                cve = item.get("cve") if isinstance(item, dict) else None
                if not isinstance(cve, dict):
                    result.record_errors.append("entrada sin objeto 'cve'")
                    continue
                if cve.get("vulnStatus") == "Rejected":
                    continue  # CVE retirada por su CNA: no aporta nada consultable
                try:
                    result.vulnerabilities.append(parse_cve(cve))
                except (KeyError, TypeError, ValueError, ArithmeticError, ValidationError) as exc:
                    result.record_errors.append(
                        f"{cve.get('id', 'entrada sin id')}: {describe_error(exc)}"
                    )

            page_size = len(data["vulnerabilities"])
            start_index += page_size
            if page_size == 0 or start_index >= int(data.get("totalResults", 0)):
                return result
            await self._sleep(delay)
