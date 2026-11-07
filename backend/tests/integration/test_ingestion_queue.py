from datetime import UTC, date, datetime, timedelta

import pytest

from app.connectors import ConnectorError, FetchResult
from app.domain.enums import IndicatorType, IngestionStatus, TriggerType
from app.domain.records import IndicatorRecord, ObservationRecord, VulnerabilityRecord
from app.repositories import ingestion_runs
from app.repositories.sources import get_by_provider_key
from app.repositories.vulnerabilities import get_by_cve_id, upsert_vulnerabilities
from app.services.ingestion import execute_run


@pytest.fixture
def kev(db_session):
    return get_by_provider_key(db_session, "cisa_kev")


def kev_record(cve_id: str) -> VulnerabilityRecord:
    return VulnerabilityRecord(
        cve_id=cve_id, is_known_exploited=True, kev_added_at=date(2024, 1, 1)
    )


def fetcher_returning(result: FetchResult):
    async def fetch(provider_key, since, settings):
        return result

    return fetch


def test_only_one_active_run_per_source(db_session, kev):
    first = ingestion_runs.request_run(db_session, kev, TriggerType.MANUAL)
    with pytest.raises(ingestion_runs.ActiveRunExistsError) as info:
        ingestion_runs.request_run(db_session, kev, TriggerType.SCHEDULED)
    assert info.value.active_run.id == first.id

    nvd = get_by_provider_key(db_session, "nvd")
    ingestion_runs.request_run(db_session, nvd, TriggerType.MANUAL)  # otra fuente sí puede


def test_claim_takes_oldest_pending(db_session, kev):
    nvd = get_by_provider_key(db_session, "nvd")
    first = ingestion_runs.request_run(db_session, kev, TriggerType.MANUAL)
    ingestion_runs.request_run(db_session, nvd, TriggerType.MANUAL)

    claimed = ingestion_runs.claim_next_pending(db_session)
    assert claimed.id == first.id
    assert claimed.status is IngestionStatus.RUNNING
    assert claimed.started_at is not None and claimed.claimed_at is not None
    assert kev.last_attempt_at is not None


def test_claim_returns_none_when_queue_is_empty(db_session):
    assert ingestion_runs.claim_next_pending(db_session) is None


def test_stale_runs_are_failed(db_session, kev):
    run = ingestion_runs.start_run(db_session, kev, TriggerType.SCHEDULED)
    run.started_at = datetime.now(UTC) - timedelta(hours=3)
    db_session.flush()

    stale = ingestion_runs.fail_stale_runs(db_session, timedelta(hours=1))
    assert [r.id for r in stale] == [run.id]
    assert run.status is IngestionStatus.FAILED
    assert kev.last_error


def test_execute_run_persists_and_is_idempotent(db_session, kev):
    result = FetchResult(
        vulnerabilities=[kev_record("CVE-2024-0001"), kev_record("CVE-2024-0002")],
        kev_catalog={"CVE-2024-0001", "CVE-2024-0002"},
    )
    run = ingestion_runs.start_run(db_session, kev, TriggerType.MANUAL)
    execute_run(db_session, run, fetcher_returning(result))
    assert run.status is IngestionStatus.COMPLETED
    assert (run.records_created, run.records_updated) == (2, 0)
    assert kev.last_success_at is not None

    again = ingestion_runs.start_run(db_session, kev, TriggerType.MANUAL)
    execute_run(db_session, again, fetcher_returning(result))
    assert (again.records_created, again.records_updated, again.records_processed) == (0, 0, 2)


def test_full_kev_sync_clears_removed_cves(db_session, kev):
    upsert_vulnerabilities(db_session, [kev_record("CVE-2024-0001"), kev_record("CVE-2024-0002")])
    result = FetchResult(
        vulnerabilities=[kev_record("CVE-2024-0001")], kev_catalog={"CVE-2024-0001"}
    )
    run = ingestion_runs.start_run(db_session, kev, TriggerType.SCHEDULED)
    execute_run(db_session, run, fetcher_returning(result))

    assert get_by_cve_id(db_session, "CVE-2024-0001").is_known_exploited is True
    assert get_by_cve_id(db_session, "CVE-2024-0002").is_known_exploited is False
    assert run.records_updated == 1


def test_record_errors_make_run_partial(db_session):
    urlhaus = get_by_provider_key(db_session, "urlhaus")
    obs = ObservationRecord(
        indicator=IndicatorRecord.from_value(IndicatorType.URL, "http://evil.example/a"),
        external_id="10",
    )
    result = FetchResult(observations=[obs], record_errors=["id 11: URL inválida"])
    run = ingestion_runs.start_run(db_session, urlhaus, TriggerType.MANUAL)
    execute_run(db_session, run, fetcher_returning(result))

    assert run.status is IngestionStatus.PARTIAL
    assert run.error_count == 1
    assert "URL inválida" in run.error_summary
    assert run.records_created == 1


def test_source_failure_keeps_previous_data(db_session, kev):
    upsert_vulnerabilities(db_session, [kev_record("CVE-2024-0001")])

    async def failing(provider_key, since, settings):
        raise ConnectorError("cisa_kev respondió HTTP 503 (Service Unavailable)")

    run = ingestion_runs.start_run(db_session, kev, TriggerType.MANUAL)
    execute_run(db_session, run, failing)

    assert run.status is IngestionStatus.FAILED
    assert "503" in run.error_summary
    assert get_by_cve_id(db_session, "CVE-2024-0001").is_known_exploited is True
