from collections.abc import Iterable

from sqlalchemy import func, literal_column, select, tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.domain.enums import IndicatorType
from app.domain.records import IndicatorRecord, ObservationRecord
from app.models import Indicator, Observation
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
