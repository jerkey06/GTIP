"""Conectores probados con respuestas de ejemplo, sin llamar a las APIs reales (ADD §16.1)."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import httpx
import pytest
import respx

from app.connectors import ConnectorError, unavailable_reason
from app.connectors.cisa_kev import FEED_URL, CisaKevConnector
from app.connectors.nvd import API_URL, NvdConnector
from app.connectors.urlhaus import API_URL as URLHAUS_API_URL
from app.connectors.urlhaus import UrlhausConnector
from app.core.config import Settings
from app.domain.enums import IndicatorType

KEV_FEED = {
    "title": "CISA Catalog of Known Exploited Vulnerabilities",
    "count": 2,
    "vulnerabilities": [
        {
            "cveID": "CVE-2024-3400",
            "vendorProject": "Palo Alto Networks",
            "product": "PAN-OS",
            "vulnerabilityName": "Palo Alto Networks PAN-OS Command Injection Vulnerability",
            "dateAdded": "2024-04-12",
            "shortDescription": "Command injection in GlobalProtect.",
            "requiredAction": "Apply mitigations per vendor instructions.",
            "dueDate": "2024-04-19",
            "knownRansomwareCampaignUse": "Unknown",
        },
        {
            "cveID": "cve-2021-44228",
            "vendorProject": "Apache",
            "product": "Log4j2",
            "vulnerabilityName": "Apache Log4j2 RCE",
            "dateAdded": "2021-12-10",
            "shortDescription": "",
            "requiredAction": "Apply updates.",
            "dueDate": "2021-12-24",
        },
    ],
}


def nvd_item(cve_id: str, **extra) -> dict:
    cve = {
        "id": cve_id,
        "published": "2024-04-12T08:15:06.230",
        "lastModified": "2024-04-15T10:00:00.000",
        "vulnStatus": "Analyzed",
        "descriptions": [
            {"lang": "es", "value": "Descripción"},
            {"lang": "en", "value": "  A command injection vulnerability.  "},
        ],
        "metrics": {
            "cvssMetricV31": [
                {
                    "source": "psirt@paloaltonetworks.com",
                    "type": "Secondary",
                    "cvssData": {"version": "3.1", "baseScore": 10.0, "vectorString": "X"},
                },
                {
                    "source": "nvd@nist.gov",
                    "type": "Primary",
                    "cvssData": {
                        "version": "3.1",
                        "baseScore": 9.8,
                        "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    },
                },
            ]
        },
        "references": [{"url": "https://security.example/advisory", "source": "x", "tags": []}],
    }
    cve.update(extra)
    return {"cve": cve}


URLHAUS_JSON = {
    "query_status": "ok",
    "urls": [
        {
            "id": "3001",
            "urlhaus_reference": "https://urlhaus.abuse.ch/url/3001/",
            "url": "http://Evil.Example:80/bin.sh",
            "url_status": "online",
            "date_added": "2026-10-30 10:00:00 UTC",
            "last_online": "2026-10-31 12:00:00",
            "threat": "malware_download",
            "tags": ["elf", "mirai"],
            "reporter": "reporter1",
        },
        {
            "id": "3002",
            "urlhaus_reference": "https://urlhaus.abuse.ch/url/3002/",
            "url": "esto no es una url",
            "url_status": "offline",
            "date_added": "2026-10-30 11:00:00 UTC",
            "last_online": None,
            "threat": "malware_download",
            "tags": None,
            "reporter": "reporter2",
        },
    ],
}


async def no_sleep(_: float) -> None:
    return None


@pytest.fixture
def settings():
    return Settings(app_secret_key="x" * 40, ingestion_max_retries=2)


async def run(connector_cls, settings, since=None):
    async with httpx.AsyncClient() as client:
        return await connector_cls(client, settings, sleep=no_sleep).fetch(since)


@respx.mock
async def test_cisa_kev_parses_full_catalog(settings):
    respx.get(FEED_URL).respond(json=KEV_FEED)
    result = await run(CisaKevConnector, settings)

    assert [v.cve_id for v in result.vulnerabilities] == ["CVE-2024-3400", "CVE-2021-44228"]
    first = result.vulnerabilities[0]
    assert first.is_known_exploited is True
    assert first.kev_added_at == date(2024, 4, 12)
    assert first.kev_due_date == date(2024, 4, 19)
    assert first.kev_vendor_project == "Palo Alto Networks"
    assert first.description is None  # la descripción completa la aporta NVD
    assert result.vulnerabilities[1].kev_short_description is None
    assert result.kev_catalog == {"CVE-2024-3400", "CVE-2021-44228"}
    assert result.record_errors == []


@respx.mock
async def test_cisa_kev_invalid_entry_makes_catalog_incomplete(settings):
    feed = {"vulnerabilities": [*KEV_FEED["vulnerabilities"], {"cveID": "no-es-cve"}]}
    respx.get(FEED_URL).respond(json=feed)
    result = await run(CisaKevConnector, settings)

    assert len(result.vulnerabilities) == 2
    assert len(result.record_errors) == 1
    assert result.kev_catalog is None  # no se puede quitar la marca KEV a nadie


@respx.mock
async def test_cisa_kev_rejects_unexpected_format(settings):
    respx.get(FEED_URL).respond(json={"otra": "cosa"})
    with pytest.raises(ConnectorError):
        await run(CisaKevConnector, settings)


@respx.mock
async def test_transient_errors_are_retried(settings):
    route = respx.get(FEED_URL)
    route.side_effect = [
        httpx.Response(503),
        httpx.ConnectError("caída"),
        httpx.Response(200, json=KEV_FEED),
    ]
    result = await run(CisaKevConnector, settings)
    assert route.call_count == 3
    assert len(result.vulnerabilities) == 2


@respx.mock
async def test_client_errors_are_not_retried_and_hide_secrets(settings):
    settings.nvd_api_key = "CLAVE-SECRETA"
    route = respx.get(API_URL).respond(403)
    with pytest.raises(ConnectorError) as info:
        await run(NvdConnector, settings)
    assert route.call_count == 1
    assert "CLAVE-SECRETA" not in str(info.value)
    assert route.calls[0].request.headers["apiKey"] == "CLAVE-SECRETA"


@respx.mock
async def test_retries_are_limited(settings):
    route = respx.get(FEED_URL).respond(500)
    with pytest.raises(ConnectorError):
        await run(CisaKevConnector, settings)
    assert route.call_count == settings.ingestion_max_retries + 1


@respx.mock
async def test_nvd_paginates_and_normalizes(settings):
    pages = [
        {
            "totalResults": 3,
            "vulnerabilities": [nvd_item("CVE-2024-3400"), nvd_item("CVE-2024-0001")],
        },
        {
            "totalResults": 3,
            "vulnerabilities": [nvd_item("CVE-2024-0002", vulnStatus="Rejected", metrics={})],
        },
    ]
    route = respx.get(API_URL)
    route.side_effect = [httpx.Response(200, json=p) for p in pages]

    result = await run(NvdConnector, settings)

    assert route.call_count == 2
    assert route.calls[1].request.url.params["startIndex"] == "2"
    assert [v.cve_id for v in result.vulnerabilities] == ["CVE-2024-3400", "CVE-2024-0001"]
    vuln = result.vulnerabilities[0]
    assert vuln.description == "A command injection vulnerability."
    assert vuln.cvss_score == Decimal("9.8")  # la métrica Primary
    assert vuln.cvss_version == "3.1"
    assert vuln.cvss_vector.startswith("CVSS:3.1/")
    assert vuln.published_at == datetime(2024, 4, 12, 8, 15, 6, 230000, tzinfo=UTC)
    assert vuln.is_known_exploited is None  # NVD no decide sobre KEV
    assert vuln.nvd_references[0]["url"] == "https://security.example/advisory"


@respx.mock
async def test_nvd_without_metrics_keeps_cvss_unknown(settings):
    respx.get(API_URL).respond(
        json={"totalResults": 1, "vulnerabilities": [nvd_item("CVE-2024-0003", metrics={})]}
    )
    result = await run(NvdConnector, settings)
    assert result.vulnerabilities[0].cvss_score is None


def test_nvd_window_is_incremental_and_capped(settings):
    connector = NvdConnector(httpx.AsyncClient(), settings)
    now = datetime(2026, 11, 2, tzinfo=UTC)

    start, end = connector.window(None, now)
    assert (end - start) == timedelta(days=settings.nvd_initial_days)

    start, _ = connector.window(now - timedelta(hours=2), now)
    assert start == now - timedelta(hours=2, minutes=15)

    start, _ = connector.window(now - timedelta(days=400), now)
    assert start == now - timedelta(days=120)


@respx.mock
async def test_urlhaus_parses_json_and_skips_invalid_entries(settings):
    settings.urlhaus_auth_key = "clave-de-prueba"
    route = respx.get(URLHAUS_API_URL).respond(json=URLHAUS_JSON)
    result = await run(UrlhausConnector, settings)

    assert route.calls.last.request.headers["Auth-Key"] == "clave-de-prueba"
    assert len(result.observations) == 1
    assert len(result.record_errors) == 1
    obs = result.observations[0]
    assert obs.indicator.indicator_type is IndicatorType.URL
    assert obs.indicator.normalized_value == "http://evil.example/bin.sh"
    assert obs.indicator.value == "http://Evil.Example:80/bin.sh"
    assert obs.external_id == "3001"
    assert obs.first_seen_at == datetime(2026, 10, 30, 10, tzinfo=UTC)
    assert obs.last_seen_at == datetime(2026, 10, 31, 12, tzinfo=UTC)
    assert obs.reference_url == "https://urlhaus.abuse.ch/url/3001/"
    assert obs.source_data["tags"] == ["elf", "mirai"]
    assert obs.source_data["threat"] == "malware_download"


@respx.mock
async def test_urlhaus_unexpected_status_is_an_error(settings):
    settings.urlhaus_auth_key = "clave-de-prueba"
    respx.get(URLHAUS_API_URL).respond(json={"query_status": "unknown_auth_key"})
    with pytest.raises(ConnectorError):
        await run(UrlhausConnector, settings)


@respx.mock
async def test_urlhaus_html_response_is_an_error(settings):
    settings.urlhaus_auth_key = "clave-de-prueba"
    respx.get(URLHAUS_API_URL).respond(text="<html><body>Forbidden</body></html>")
    with pytest.raises(ConnectorError):
        await run(UrlhausConnector, settings)


def test_urlhaus_needs_auth_key(settings):
    settings.urlhaus_auth_key = None
    assert "URLHAUS_AUTH_KEY" in unavailable_reason("urlhaus", settings)
    settings.urlhaus_auth_key = "clave"
    assert unavailable_reason("urlhaus", settings) is None


def test_unavailable_reasons(settings):
    assert unavailable_reason("cisa_kev", settings) is None
    settings.cisa_kev_enabled = False
    assert "CISA_KEV_ENABLED" in unavailable_reason("cisa_kev", settings)
    assert unavailable_reason("abuseipdb", settings) == "Falta ABUSEIPDB_API_KEY"
    settings.abuseipdb_api_key = "clave"
    assert "pendiente" in unavailable_reason("abuseipdb", settings)
