from collections.abc import Iterable

from sqlalchemy import func, literal_column, select, tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.domain.records import VulnerabilityRecord
from app.models import Vulnerability
from app.repositories._upsert import UpsertResult, chunks

# Campos que una fuente puede actualizar. Si llegan en None se conserva lo guardado.
_MERGEABLE = (
    "description",
    "cvss_score",
    "cvss_version",
    "cvss_vector",
    "published_at",
    "modified_at",
    "kev_added_at",
)


def get_by_cve_id(session: Session, cve_id: str) -> Vulnerability | None:
    return session.scalar(select(Vulnerability).where(Vulnerability.cve_id == cve_id.upper()))


def upsert_vulnerabilities(
    session: Session, records: Iterable[VulnerabilityRecord], batch_size: int = 500
) -> UpsertResult:
    """Inserta o actualiza por ``cve_id`` de forma idempotente (ADD §9.2 y §13.3).

    - Repetir la misma importación no crea filas ni cuenta actualizaciones.
    - Un campo en None no borra el valor existente: KEV y NVD se complementan.
    - ``is_known_exploited`` solo cambia cuando el registro lo trae explícitamente.

    No hace commit: la transacción la controla quien llama.
    """
    latest = {record.cve_id: record for record in records}  # dentro de un lote, gana el último
    with_kev = [r for r in latest.values() if r.is_known_exploited is not None]
    without_kev = [r for r in latest.values() if r.is_known_exploited is None]

    result = UpsertResult()
    for group, include_kev in ((with_kev, True), (without_kev, False)):
        for batch in chunks(group, batch_size):
            result += _upsert_batch(session, batch, include_kev)
    return result


def _upsert_batch(
    session: Session, batch: list[VulnerabilityRecord], include_kev: bool
) -> UpsertResult:
    columns = {"cve_id", *_MERGEABLE} | ({"is_known_exploited"} if include_kev else set())
    rows = [record.model_dump(include=columns) for record in batch]

    table = Vulnerability.__table__
    stmt = pg_insert(table).values(rows)
    new_values = {c: func.coalesce(stmt.excluded[c], table.c[c]) for c in _MERGEABLE}
    if include_kev:
        new_values["is_known_exploited"] = stmt.excluded.is_known_exploited

    changed = tuple_(*(table.c[c] for c in new_values)).is_distinct_from(
        tuple_(*new_values.values())
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[table.c.cve_id],
        set_={**new_values, "updated_at": func.now()},
        where=changed,
    ).returning(literal_column("xmax = 0").label("inserted"))

    # RETURNING solo devuelve filas insertadas (xmax = 0) o realmente modificadas.
    inserted_flags = session.execute(stmt).scalars().all()
    created = sum(1 for flag in inserted_flags if flag)
    updated = len(inserted_flags) - created
    return UpsertResult(
        created=created, updated=updated, unchanged=len(batch) - len(inserted_flags)
    )
