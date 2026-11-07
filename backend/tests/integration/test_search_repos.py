from datetime import UTC, datetime
from decimal import Decimal

from app.domain.enums import IndicatorType
from app.domain.records import IndicatorRecord, ObservationRecord, VulnerabilityRecord
from app.repositories.indicators import (
    IndicatorFilters,
    list_observations,
    search_indicators,
    upsert_observations,
)
from app.repositories.sources import get_by_provider_key
from app.repositories.vulnerabilities import (
    VulnerabilityFilters,
    VulnerabilitySort,
    search_vulnerabilities,
    upsert_vulnerabilities,
)


def test_like_wildcards_from_user_are_literal(db_session):
    upsert_vulnerabilities(
        db_session,
        [
            VulnerabilityRecord(cve_id="CVE-2024-0001", description="100% remoto"),
            VulnerabilityRecord(cve_id="CVE-2024-0002", description="1000 usuarios"),
        ],
    )
    items, total = search_vulnerabilities(
        db_session, VulnerabilityFilters(q="100%"), VulnerabilitySort.PUBLISHED_DESC, 0, 10
    )
    assert total == 1
    assert items[0].cve_id == "CVE-2024-0001"


def test_sort_by_cvss_puts_unscored_last(db_session):
    upsert_vulnerabilities(
        db_session,
        [
            VulnerabilityRecord(cve_id="CVE-2024-0001"),
            VulnerabilityRecord(cve_id="CVE-2024-0002", cvss_score=Decimal("4.3")),
            VulnerabilityRecord(cve_id="CVE-2024-0003", cvss_score=Decimal("9.1")),
        ],
    )
    items, _ = search_vulnerabilities(
        db_session, VulnerabilityFilters(), VulnerabilitySort.CVSS_DESC, 0, 10
    )
    assert [v.cve_id for v in items] == ["CVE-2024-0003", "CVE-2024-0002", "CVE-2024-0001"]


def test_indicator_counts_and_source_filter(db_session):
    urlhaus = get_by_provider_key(db_session, "urlhaus")
    nvd = get_by_provider_key(db_session, "nvd")
    indicator = IndicatorRecord.from_value(
        IndicatorType.URL, "http://evil.example/a", last_seen_at=datetime(2026, 1, 1, tzinfo=UTC)
    )
    upsert_observations(
        db_session,
        urlhaus.id,
        [
            ObservationRecord(indicator=indicator, external_id="1"),
            ObservationRecord(indicator=indicator, external_id="2"),
        ],
    )
    upsert_observations(db_session, nvd.id, [ObservationRecord(indicator=indicator)])

    items, total = search_indicators(db_session, IndicatorFilters(), 0, 10)
    assert total == 1
    assert (items[0].source_count, items[0].observation_count) == (2, 3)

    _, by_source = search_indicators(db_session, IndicatorFilters(source_id=urlhaus.id), 0, 10)
    assert by_source == 1
    otx = get_by_provider_key(db_session, "otx")
    _, none = search_indicators(db_session, IndicatorFilters(source_id=otx.id), 0, 10)
    assert none == 0

    observations = list_observations(db_session, items[0].indicator.id)
    assert {o.source.provider_key for o in observations} == {"urlhaus", "nvd"}
