from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.domain.enums import IndicatorType
from app.domain.records import IndicatorRecord, ObservationRecord
from app.models import Indicator, Observation, Source
from app.repositories.indicators import get_indicator, upsert_observations
from app.repositories.sources import get_by_provider_key

URL = IndicatorRecord(
    indicator_type=IndicatorType.URL,
    value="http://Malo.example/payload.exe",
    normalized_value="http://malo.example/payload.exe",
    first_seen_at=datetime(2024, 3, 1, tzinfo=UTC),
    last_seen_at=datetime(2024, 3, 5, tzinfo=UTC),
)


def _observation(**changes) -> ObservationRecord:
    base = ObservationRecord(
        indicator=URL,
        external_id="3001",
        reference_url="https://urlhaus.abuse.ch/url/3001/",
        source_data={"threat": "malware_download"},
    )
    return base.model_copy(update=changes)


@pytest.fixture
def urlhaus(db_session) -> Source:
    return get_by_provider_key(db_session, "urlhaus")


def _count(session, model) -> int:
    return session.scalar(select(func.count()).select_from(model))


def test_initial_sources_are_seeded(db_session):
    keys = set(db_session.scalars(select(Source.provider_key)))
    assert keys == {"cisa_kev", "nvd", "urlhaus", "abuseipdb", "otx"}


def test_observation_upsert_is_idempotent(db_session, urlhaus):
    first = upsert_observations(db_session, urlhaus.id, [_observation()])
    again = upsert_observations(db_session, urlhaus.id, [_observation()])

    assert (first.created, again.created, again.updated, again.unchanged) == (1, 0, 0, 1)
    assert _count(db_session, Indicator) == 1
    assert _count(db_session, Observation) == 1


def test_changed_source_data_updates_observation(db_session, urlhaus):
    upsert_observations(db_session, urlhaus.id, [_observation()])
    result = upsert_observations(
        db_session, urlhaus.id, [_observation(source_data={"threat": "offline"})]
    )
    assert result.updated == 1
    obs = db_session.scalar(select(Observation))
    db_session.refresh(obs)
    assert obs.source_data == {"threat": "offline"}


def test_observations_without_external_id_are_not_duplicated(db_session, urlhaus):
    upsert_observations(db_session, urlhaus.id, [_observation(external_id=None)])
    upsert_observations(db_session, urlhaus.id, [_observation(external_id=None)])
    assert _count(db_session, Observation) == 1


def test_same_indicator_from_two_sources_shares_identity(db_session, urlhaus):
    otx = get_by_provider_key(db_session, "otx")
    upsert_observations(db_session, urlhaus.id, [_observation()])
    upsert_observations(db_session, otx.id, [_observation(external_id="pulse-1")])
    assert _count(db_session, Indicator) == 1
    assert _count(db_session, Observation) == 2


def test_indicator_seen_range_widens(db_session, urlhaus):
    later = URL.model_copy(
        update={
            "first_seen_at": datetime(2024, 3, 3, tzinfo=UTC),
            "last_seen_at": datetime(2024, 4, 1, tzinfo=UTC),
        }
    )
    upsert_observations(db_session, urlhaus.id, [_observation()])
    upsert_observations(db_session, urlhaus.id, [_observation(indicator=later, external_id="2")])

    indicator = get_indicator(db_session, IndicatorType.URL, URL.normalized_value)
    db_session.refresh(indicator)
    assert indicator.first_seen_at == datetime(2024, 3, 1, tzinfo=UTC)
    assert indicator.last_seen_at == datetime(2024, 4, 1, tzinfo=UTC)


def test_database_rejects_unknown_indicator_type(db_session):
    db_session.add(Indicator(indicator_type="email", value="a@b.c", normalized_value="a@b.c"))
    with pytest.raises(Exception):  # noqa: B017  (LookupError en Python o CHECK en PostgreSQL)
        db_session.flush()


def test_database_enforces_indicator_uniqueness(db_session):
    for _ in range(2):
        db_session.add(
            Indicator(indicator_type=IndicatorType.DOMAIN, value="x.com", normalized_value="x.com")
        )
    with pytest.raises(IntegrityError):
        db_session.flush()
