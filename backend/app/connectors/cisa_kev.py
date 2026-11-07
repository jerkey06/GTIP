"""CISA Known Exploited Vulnerabilities: catálogo completo en un único JSON público."""

from datetime import date, datetime
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

FEED_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


def _date(value: Any) -> date | None:
    if not value:
        return None
    return date.fromisoformat(str(value)[:10])


def _text(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def parse_entry(entry: dict[str, Any]) -> VulnerabilityRecord:
    return VulnerabilityRecord(
        cve_id=entry["cveID"],
        is_known_exploited=True,
        kev_added_at=_date(entry.get("dateAdded")),
        kev_short_description=_text(entry.get("shortDescription")),
        kev_vendor_project=_text(entry.get("vendorProject")),
        kev_product=_text(entry.get("product")),
        kev_vulnerability_name=_text(entry.get("vulnerabilityName")),
        kev_required_action=_text(entry.get("requiredAction")),
        kev_due_date=_date(entry.get("dueDate")),
    )


class CisaKevConnector(Connector):
    provider_key = "cisa_kev"

    @classmethod
    def unavailable_reason(cls, settings: Settings) -> str | None:
        if not settings.cisa_kev_enabled:
            return "Desactivada con CISA_KEV_ENABLED=false"
        return None

    async def fetch(self, since: datetime | None) -> FetchResult:
        # El catálogo es pequeño (unos miles de entradas): siempre se descarga entero,
        # así también se detectan las CVE que salen del catálogo.
        data = json_body(await self.get(FEED_URL), self.provider_key)
        entries = data.get("vulnerabilities") if isinstance(data, dict) else None
        if not isinstance(entries, list):
            raise ConnectorError("cisa_kev: la respuesta no contiene la lista 'vulnerabilities'")

        result = FetchResult()
        for entry in entries:
            try:
                result.vulnerabilities.append(parse_entry(entry))
            except (KeyError, TypeError, ValueError, ValidationError) as exc:
                cve = entry.get("cveID") if isinstance(entry, dict) else None
                result.record_errors.append(f"{cve or 'entrada sin cveID'}: {describe_error(exc)}")

        # Solo se considera completo si no se descartó nada: si no, una CVE inválida
        # perdería su marca KEV por error.
        if not result.record_errors:
            result.kev_catalog = {v.cve_id for v in result.vulnerabilities}
        return result
