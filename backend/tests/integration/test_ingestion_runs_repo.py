import pytest

from app.core.config import get_settings
from app.domain.enums import IngestionStatus, TriggerType
from app.repositories._upsert import UpsertResult
from app.repositories.ingestion_runs import finish_run, start_run
from app.repositories.sources import get_by_provider_key


@pytest.fixture
def kev(db_session):
    return get_by_provider_key(db_session, "cisa_kev")


def test_successful_run_updates_counts_and_source(db_session, kev):
    run = start_run(db_session, kev, TriggerType.MANUAL)
    assert run.status is IngestionStatus.RUNNING
    assert kev.last_attempt_at is not None

    finish_run(
        db_session, run, IngestionStatus.COMPLETED, UpsertResult(created=3, updated=1, unchanged=6)
    )
    assert (run.records_processed, run.records_created, run.records_updated) == (10, 3, 1)
    assert run.finished_at is not None
    assert kev.last_success_at == run.finished_at
    assert kev.last_error is None


def test_failed_run_keeps_last_success(db_session, kev):
    finish_run(
        db_session, start_run(db_session, kev, TriggerType.SCHEDULED), IngestionStatus.COMPLETED
    )
    previous_success = kev.last_success_at

    run = start_run(db_session, kev, TriggerType.SCHEDULED)
    finish_run(db_session, run, IngestionStatus.FAILED, error_count=1, error_summary="timeout")
    assert kev.last_success_at == previous_success
    assert kev.last_error == "timeout"


def test_error_summary_hides_api_keys(db_session, kev, monkeypatch):
    monkeypatch.setattr(get_settings(), "nvd_api_key", "SECRETO-123")
    run = start_run(db_session, kev, TriggerType.MANUAL)
    finish_run(
        db_session, run, IngestionStatus.FAILED, error_summary="GET ...?apiKey=SECRETO-123 -> 403"
    )
    assert "SECRETO-123" not in run.error_summary


def test_non_final_status_is_rejected(db_session, kev):
    run = start_run(db_session, kev, TriggerType.MANUAL)
    with pytest.raises(ValueError):
        finish_run(db_session, run, IngestionStatus.RUNNING)
