from datetime import UTC, date, datetime
from decimal import Decimal

from app.domain.records import VulnerabilityRecord
from app.repositories.vulnerabilities import get_by_cve_id, upsert_vulnerabilities

KEV = VulnerabilityRecord(
    cve_id="CVE-2024-0001",
    description="Descripción corta de KEV",
    is_known_exploited=True,
    kev_added_at=date(2024, 5, 1),
)
NVD = VulnerabilityRecord(
    cve_id="CVE-2024-0001",
    description="Descripción completa de NVD",
    cvss_score=Decimal("9.8"),
    cvss_version="3.1",
    published_at=datetime(2024, 4, 1, tzinfo=UTC),
)


def test_insert_then_repeat_is_idempotent(db_session):
    first = upsert_vulnerabilities(db_session, [KEV])
    assert (first.created, first.updated, first.unchanged) == (1, 0, 0)

    again = upsert_vulnerabilities(db_session, [KEV])
    assert (again.created, again.updated, again.unchanged) == (0, 0, 1)


def test_sources_complement_without_erasing(db_session):
    upsert_vulnerabilities(db_session, [KEV])
    result = upsert_vulnerabilities(db_session, [NVD])
    assert result.updated == 1

    vuln = get_by_cve_id(db_session, "CVE-2024-0001")
    assert vuln.is_known_exploited is True  # NVD no dice nada de KEV: se conserva
    assert vuln.kev_added_at == date(2024, 5, 1)
    assert vuln.cvss_score == Decimal("9.8")
    assert vuln.description == "Descripción completa de NVD"


def test_missing_cvss_stays_null(db_session):
    upsert_vulnerabilities(db_session, [KEV])
    assert get_by_cve_id(db_session, "CVE-2024-0001").cvss_score is None


def test_kev_flag_can_be_cleared_explicitly(db_session):
    upsert_vulnerabilities(db_session, [KEV])
    removed = KEV.model_copy(update={"is_known_exploited": False})
    upsert_vulnerabilities(db_session, [removed])
    assert get_by_cve_id(db_session, "CVE-2024-0001").is_known_exploited is False


def test_duplicates_in_same_batch_are_merged(db_session):
    newer = KEV.model_copy(update={"description": "Más reciente"})
    result = upsert_vulnerabilities(db_session, [KEV, newer])
    assert result.created == 1
    assert get_by_cve_id(db_session, "CVE-2024-0001").description == "Más reciente"


def test_large_input_is_split_in_batches(db_session):
    records = [VulnerabilityRecord(cve_id=f"CVE-2023-{i:05d}") for i in range(1, 1201)]
    result = upsert_vulnerabilities(db_session, records, batch_size=500)
    assert result.created == 1200
