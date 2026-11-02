from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.domain.enums import IndicatorType, IngestionStatus, TriggerType
from app.domain.records import IndicatorRecord, ObservationRecord, VulnerabilityRecord
from app.main import app
from app.repositories import ingestion_runs
from app.repositories.indicators import upsert_observations
from app.repositories.sources import get_by_provider_key
from app.repositories.vulnerabilities import upsert_vulnerabilities

PROTECTED = [
    "/api/v1/dashboard",
    "/api/v1/sources",
    "/api/v1/vulnerabilities",
    "/api/v1/indicators",
    "/api/v1/ingestions",
    "/api/v1/search?q=x",
]


@pytest.fixture
def data(db_session):
    upsert_vulnerabilities(
        db_session,
        [
            VulnerabilityRecord(
                cve_id="CVE-2024-3400",
                description="Command injection in PAN-OS",
                cvss_score=Decimal("10.0"),
                cvss_version="3.1",
                published_at=datetime(2024, 4, 12, tzinfo=UTC),
                is_known_exploited=True,
                kev_added_at=date(2024, 4, 12),
                kev_vendor_project="Palo Alto Networks",
                nvd_references=[{"url": "https://example.org/a", "source": "x", "tags": []}],
            ),
            VulnerabilityRecord(
                cve_id="CVE-2024-0001",
                description="Sin puntuación todavía",
                published_at=datetime(2024, 1, 1, tzinfo=UTC),
            ),
            VulnerabilityRecord(
                cve_id="CVE-2023-0002",
                description="Media",
                cvss_score=Decimal("5.0"),
                published_at=datetime(2023, 6, 1, tzinfo=UTC),
            ),
        ],
    )
    urlhaus = get_by_provider_key(db_session, "urlhaus")
    upsert_observations(
        db_session,
        urlhaus.id,
        [
            ObservationRecord(
                indicator=IndicatorRecord.from_value(IndicatorType.URL, "http://Evil.Example/x"),
                external_id="1",
                reference_url="https://urlhaus.abuse.ch/url/1/",
                source_data={"threat": "malware_download"},
            )
        ],
    )
    db_session.commit()


@pytest.mark.parametrize("path", PROTECTED)
def test_business_endpoints_require_auth(db_session, path):
    from app.db.session import get_db

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        assert TestClient(app).get(path).status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_ready_checks_database(auth_client):
    body = auth_client.get("/api/v1/health/ready").json()
    assert body["database"] == "ok"


def test_list_vulnerabilities_with_filters(auth_client, data):
    body = auth_client.get("/api/v1/vulnerabilities").json()
    assert body["total"] == 3
    assert [v["cve_id"] for v in body["items"]] == [
        "CVE-2024-3400",
        "CVE-2024-0001",
        "CVE-2023-0002",
    ]

    kev = auth_client.get("/api/v1/vulnerabilities", params={"is_kev": True}).json()
    assert [v["cve_id"] for v in kev["items"]] == ["CVE-2024-3400"]

    high = auth_client.get("/api/v1/vulnerabilities", params={"min_cvss": 7}).json()
    assert high["total"] == 1

    unscored = auth_client.get("/api/v1/vulnerabilities", params={"has_cvss": False}).json()
    assert unscored["items"][0]["cvss_score"] is None  # ausente, no 0

    text = auth_client.get("/api/v1/vulnerabilities", params={"q": "pan-os"}).json()
    assert text["total"] == 1

    paged = auth_client.get("/api/v1/vulnerabilities", params={"page": 2, "page_size": 2}).json()
    assert (paged["page"], len(paged["items"]), paged["total"]) == (2, 1, 3)


def test_vulnerability_sort_is_validated(auth_client):
    response = auth_client.get("/api/v1/vulnerabilities", params={"sort": "id; DROP TABLE"})
    assert response.status_code == 422


def test_vulnerability_detail(auth_client, data):
    body = auth_client.get("/api/v1/vulnerabilities/cve-2024-3400").json()
    assert body["cvss_score"] == 10.0
    assert body["kev"]["vendor_project"] == "Palo Alto Networks"
    assert body["references"][0]["url"] == "https://example.org/a"
    assert {p["provider_key"] for p in body["provenance"]} == {"cisa_kev", "nvd"}


def test_vulnerability_detail_errors(auth_client):
    assert auth_client.get("/api/v1/vulnerabilities/CVE-1999-0001").status_code == 404
    assert auth_client.get("/api/v1/vulnerabilities/no-es-cve").status_code == 400


def test_indicator_exact_search_normalizes_value(auth_client, data):
    body = auth_client.get(
        "/api/v1/indicators", params={"value": "HTTP://evil.example:80/x"}
    ).json()
    assert body["exact"] is True
    assert body["detected_type"] == "url"
    assert body["total"] == 1
    item = body["items"][0]
    assert item["source_count"] == 1
    assert item["observation_count"] == 1

    detail = auth_client.get(f"/api/v1/indicators/{item['id']}").json()
    assert detail["normalized_value"] == "http://evil.example/x"
    observations = auth_client.get(f"/api/v1/indicators/{item['id']}/observations").json()
    assert observations[0]["source"]["provider_key"] == "urlhaus"
    assert observations[0]["source_data"]["threat"] == "malware_download"


def test_indicator_search_without_match_and_partial(auth_client, data):
    none = auth_client.get("/api/v1/indicators", params={"value": "8.8.8.8"}).json()
    assert none["total"] == 0
    assert none["detected_type"] == "ipv4"

    partial = auth_client.get("/api/v1/indicators", params={"value": "evil"}).json()
    assert partial["exact"] is False
    assert partial["total"] == 1


def test_indicator_value_must_match_type(auth_client):
    response = auth_client.get("/api/v1/indicators", params={"value": "abc", "type": "sha256"})
    assert response.status_code == 422


def test_indicator_not_found(auth_client):
    assert auth_client.get("/api/v1/indicators/999999").status_code == 404
    assert auth_client.get("/api/v1/indicators/999999/observations").status_code == 404


def test_request_ingestion_and_conflict(auth_client, db_session, api_user):
    kev = get_by_provider_key(db_session, "cisa_kev")
    response = auth_client.post("/api/v1/ingestions", json={"source_id": kev.id})
    assert response.status_code == 202
    run = response.json()
    assert run["status"] == "pending"
    assert run["trigger_type"] == "manual"
    assert run["requested_by"]["username"] == api_user.username
    assert run["started_at"] is None

    again = auth_client.post("/api/v1/ingestions", json={"source_id": kev.id})
    assert again.status_code == 409
    assert again.json()["active_run_id"] == run["id"]

    assert auth_client.get(f"/api/v1/ingestions/{run['id']}").json()["id"] == run["id"]
    history = auth_client.get("/api/v1/ingestions", params={"status": "pending"}).json()
    assert [r["id"] for r in history["items"]] == [run["id"]]

    sources = {s["provider_key"]: s for s in auth_client.get("/api/v1/sources").json()}
    assert sources["cisa_kev"]["active_run_id"] == run["id"]
    assert sources["cisa_kev"]["last_run"]["status"] == "pending"


def test_disabled_or_missing_source_cannot_be_ingested(auth_client, db_session):
    otx = get_by_provider_key(db_session, "otx")
    assert auth_client.post("/api/v1/ingestions", json={"source_id": otx.id}).status_code == 409
    assert auth_client.post("/api/v1/ingestions", json={"source_id": 999999}).status_code == 404


def test_sources_never_expose_keys(auth_client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "nvd_api_key", "CLAVE-NVD-SECRETA")
    response = auth_client.get("/api/v1/sources")
    assert "CLAVE-NVD-SECRETA" not in response.text
    nvd = next(s for s in response.json() if s["provider_key"] == "nvd")
    assert nvd["api_key_configured"] is True
    abuse = next(s for s in response.json() if s["provider_key"] == "abuseipdb")
    assert abuse["is_enabled"] is False
    assert abuse["disabled_reason"]


def test_dashboard_reflects_stored_data(auth_client, db_session, data):
    kev = get_by_provider_key(db_session, "cisa_kev")
    run = ingestion_runs.start_run(db_session, kev, TriggerType.SCHEDULED)
    ingestion_runs.finish_run(db_session, run, IngestionStatus.COMPLETED)
    db_session.commit()

    body = auth_client.get("/api/v1/dashboard").json()
    assert body["stats"]["vulnerabilities_total"] == 3
    assert body["stats"]["vulnerabilities_kev"] == 1
    assert body["stats"]["indicators_total"] == 1
    buckets = {b["severity"]: b["count"] for b in body["cvss_distribution"]}
    assert buckets == {"critical": 1, "high": 0, "medium": 1, "low": 0, "none": 0, "unscored": 1}
    assert body["recent_indicators"][0]["source_names"] == ["URLhaus"]
    assert body["latest_runs"][0]["id"] == run.id


def test_search_detects_kind(auth_client, data):
    cve = auth_client.get("/api/v1/search", params={"q": "cve-2024-3400"}).json()
    assert cve["kind"] == "cve"
    assert cve["exact_match"] == {
        "kind": "vulnerability",
        "cve_id": "CVE-2024-3400",
        "indicator_id": None,
    }

    url = auth_client.get("/api/v1/search", params={"q": "http://evil.example/x"}).json()
    assert url["kind"] == "url"
    assert url["exact_match"]["kind"] == "indicator"

    text = auth_client.get("/api/v1/search", params={"q": "injection"}).json()
    assert text["kind"] == "text"
    assert text["vulnerabilities"]["total"] == 1
