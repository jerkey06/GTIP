from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import Select, exists, func, literal_column, select, tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session, joinedload

from app.domain.enums import IndicatorType
from app.domain.records import IndicatorRecord, ObservationRecord
from app.models import Indicator, Observation
from app.repositories._query import LIKE_ESCAPE, like_pattern
from app.repositories._upsert import UpsertResult, chunks

IndicatorKey = tuple[IndicatorType, str]


def get_indicator(
    session: Session, indicator_type: IndicatorType, normalized_value: str
) -> Indicator | None:
    return session.scalar(
        select(Indicator).where(
            Indicator.indicator_type == indicator_type,
            Indicator.normalized_value == normalized_value,
        )
    )


def upsert_indicators(
    session: Session, records: Iterable[IndicatorRecord], batch_size: int = 500
) -> dict[IndicatorKey, int]:
    """Garantiza que cada indicador exista y devuelve su id por (tipo, valor normalizado).

    Amplía ``first_seen_at``/``last_seen_at`` al rango más amplio conocido. No hace commit.
    """
    latest = {(r.indicator_type, r.normalized_value): r for r in records}
    ids: dict[IndicatorKey, int] = {}
    table = Indicator.__table__
    for batch in chunks(list(latest.values()), batch_size):
        stmt = pg_insert(table).values(
            [
                r.model_dump(
                    include={
                        "indicator_type",
                        "value",
                        "normalized_value",
                        "first_seen_at",
                        "last_seen_at",
                    }
                )
                for r in batch
            ]
        )
        # Sin WHERE: así RETURNING devuelve el id también de los que ya existían.
        # LEAST/GREATEST ignoran NULL en PostgreSQL.
        stmt = stmt.on_conflict_do_update(
            index_elements=[table.c.indicator_type, table.c.normalized_value],
            set_={
                "first_seen_at": func.least(table.c.first_seen_at, stmt.excluded.first_seen_at),
                "last_seen_at": func.greatest(table.c.last_seen_at, stmt.excluded.last_seen_at),
            },
        ).returning(table.c.id, table.c.indicator_type, table.c.normalized_value)
        for row in session.execute(stmt):
            ids[(IndicatorType(row.indicator_type), row.normalized_value)] = row.id
    return ids


def upsert_observations(
    session: Session,
    source_id: int,
    records: Iterable[ObservationRecord],
    batch_size: int = 500,
) -> UpsertResult:
    """Guarda observaciones de una fuente creando antes sus indicadores. Idempotente.

    Identidad de una observación: indicador + fuente + ``external_id``. Si la fuente no
    da ``external_id``, se guarda una sola observación por indicador y fuente.
    ``observed_at`` se renueva solo cuando la fuente cambia algún dato. No hace commit.
    """
    records = list(records)
    indicator_ids = upsert_indicators(session, (r.indicator for r in records), batch_size)

    latest: dict[tuple[int, str | None], dict] = {}
    for r in records:
        indicator_id = indicator_ids[(r.indicator.indicator_type, r.indicator.normalized_value)]
        latest[(indicator_id, r.external_id)] = {
            "indicator_id": indicator_id,
            "source_id": source_id,
            **r.model_dump(
                include={
                    "external_id",
                    "first_seen_at",
                    "last_seen_at",
                    "reference_url",
                    "source_data",
                }
            ),
        }

    rows = list(latest.values())
    with_external = [row for row in rows if row["external_id"] is not None]
    without_external = [row for row in rows if row["external_id"] is None]

    result = UpsertResult()
    for group, has_external in ((with_external, True), (without_external, False)):
        for batch in chunks(group, batch_size):
            result += _upsert_observation_batch(session, batch, has_external)
    return result


def _upsert_observation_batch(
    session: Session, batch: list[dict], has_external: bool
) -> UpsertResult:
    table = Observation.__table__
    stmt = pg_insert(table).values(batch)
    ex = stmt.excluded
    new_values = {
        "first_seen_at": func.least(table.c.first_seen_at, ex.first_seen_at),
        "last_seen_at": func.greatest(table.c.last_seen_at, ex.last_seen_at),
        "reference_url": func.coalesce(ex.reference_url, table.c.reference_url),
        "source_data": ex.source_data,
    }
    changed = tuple_(*(table.c[c] for c in new_values)).is_distinct_from(
        tuple_(*new_values.values())
    )
    if has_external:
        conflict = {
            "index_elements": [table.c.indicator_id, table.c.source_id, table.c.external_id],
            "index_where": table.c.external_id.is_not(None),
        }
    else:
        conflict = {
            "index_elements": [table.c.indicator_id, table.c.source_id],
            "index_where": table.c.external_id.is_(None),
        }
    stmt = stmt.on_conflict_do_update(
        **conflict, set_={**new_values, "observed_at": func.now()}, where=changed
    ).returning(literal_column("xmax = 0").label("inserted"))

    inserted_flags = session.execute(stmt).scalars().all()
    created = sum(1 for flag in inserted_flags if flag)
    return UpsertResult(
        created=created,
        updated=len(inserted_flags) - created,
        unchanged=len(batch) - len(inserted_flags),
    )


def get_by_id(session: Session, indicator_id: int) -> Indicator | None:
    return session.get(Indicator, indicator_id)


@dataclass(frozen=True)
class IndicatorFilters:
    indicator_type: IndicatorType | None = None
    # Valor ya normalizado: búsqueda exacta (PRD §10.3).
    normalized_value: str | None = None
    # Texto libre cuando el valor no es un indicador completo: búsqueda parcial.
    contains: str | None = None
    source_id: int | None = None


@dataclass(frozen=True)
class IndicatorSummary:
    indicator: Indicator
    source_count: int
    observation_count: int


def _counts_subquery():
    return (
        select(
            Observation.indicator_id,
            func.count(func.distinct(Observation.source_id)).label("source_count"),
            func.count(Observation.id).label("observation_count"),
        )
        .group_by(Observation.indicator_id)
        .subquery()
    )


def _apply_filters(stmt: Select, f: IndicatorFilters) -> Select:
    if f.indicator_type is not None:
        stmt = stmt.where(Indicator.indicator_type == f.indicator_type)
    if f.normalized_value is not None:
        stmt = stmt.where(Indicator.normalized_value == f.normalized_value)
    if f.contains:
        stmt = stmt.where(
            Indicator.normalized_value.ilike(like_pattern(f.contains.strip()), escape=LIKE_ESCAPE)
        )
    if f.source_id is not None:
        stmt = stmt.where(
            exists().where(
                Observation.indicator_id == Indicator.id, Observation.source_id == f.source_id
            )
        )
    return stmt


def search_indicators(
    session: Session, filters: IndicatorFilters, offset: int, limit: int
) -> tuple[list[IndicatorSummary], int]:
    """Página de indicadores, los vistos más recientemente primero, con sus contadores."""
    total = session.scalar(_apply_filters(select(func.count(Indicator.id)), filters)) or 0
    counts = _counts_subquery()
    stmt = (
        _apply_filters(
            select(
                Indicator,
                func.coalesce(counts.c.source_count, 0),
                func.coalesce(counts.c.observation_count, 0),
            ).outerjoin(counts, counts.c.indicator_id == Indicator.id),
            filters,
        )
        .order_by(
            Indicator.last_seen_at.desc().nulls_last(),
            Indicator.created_at.desc(),
            Indicator.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )
    rows = session.execute(stmt).all()
    return [IndicatorSummary(row[0], row[1], row[2]) for row in rows], total


def get_summary(session: Session, indicator_id: int) -> IndicatorSummary | None:
    indicator = get_by_id(session, indicator_id)
    if indicator is None:
        return None
    source_count, observation_count = session.execute(
        select(func.count(func.distinct(Observation.source_id)), func.count(Observation.id)).where(
            Observation.indicator_id == indicator_id
        )
    ).one()
    return IndicatorSummary(indicator, source_count, observation_count)


def list_observations(session: Session, indicator_id: int) -> list[Observation]:
    """Todas las observaciones de un indicador con su fuente, agrupables por fuente."""
    stmt = (
        select(Observation)
        .options(joinedload(Observation.source))
        .where(Observation.indicator_id == indicator_id)
        .order_by(Observation.source_id, Observation.observed_at.desc(), Observation.id.desc())
    )
    return list(session.scalars(stmt))
