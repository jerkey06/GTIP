from collections.abc import Collection, Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Select, func, literal_column, or_, select, tuple_, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.domain.records import VulnerabilityRecord
from app.models import Vulnerability
from app.repositories._query import LIKE_ESCAPE, like_pattern
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
    "kev_short_description",
    "kev_vendor_project",
    "kev_product",
    "kev_vulnerability_name",
    "kev_required_action",
    "kev_due_date",
    "nvd_references",
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


def clear_known_exploited_except(session: Session, cve_ids: Collection[str]) -> int:
    """Quita la marca KEV de las CVE que ya no están en el catálogo. Devuelve cuántas.

    Solo debe llamarse tras descargar el catálogo KEV completo (PRD §9.2). No hace commit.
    """
    stmt = (
        update(Vulnerability)
        .where(Vulnerability.is_known_exploited.is_(True))
        .values(is_known_exploited=False, updated_at=func.now())
    )
    if cve_ids:
        stmt = stmt.where(Vulnerability.cve_id.not_in(list(cve_ids)))
    return session.execute(stmt).rowcount


class VulnerabilitySort(StrEnum):
    """Órdenes admitidos. Nunca se usa el texto del usuario como SQL (ADD §11.3)."""

    PUBLISHED_DESC = "-published_at"
    PUBLISHED_ASC = "published_at"
    MODIFIED_DESC = "-modified_at"
    CVSS_DESC = "-cvss_score"
    CREATED_DESC = "-created_at"


_SORT_COLUMNS = {
    VulnerabilitySort.PUBLISHED_DESC: Vulnerability.published_at.desc().nulls_last(),
    VulnerabilitySort.PUBLISHED_ASC: Vulnerability.published_at.asc().nulls_last(),
    VulnerabilitySort.MODIFIED_DESC: Vulnerability.modified_at.desc().nulls_last(),
    VulnerabilitySort.CVSS_DESC: Vulnerability.cvss_score.desc().nulls_last(),
    VulnerabilitySort.CREATED_DESC: Vulnerability.created_at.desc(),
}


@dataclass(frozen=True)
class VulnerabilityFilters:
    q: str | None = None
    is_kev: bool | None = None
    min_cvss: Decimal | None = None
    max_cvss: Decimal | None = None
    has_cvss: bool | None = None
    published_after: datetime | None = None
    published_before: datetime | None = None


def _apply_filters(stmt: Select, f: VulnerabilityFilters) -> Select:
    if f.q:
        pattern = like_pattern(f.q.strip())
        stmt = stmt.where(
            or_(
                *(
                    column.ilike(pattern, escape=LIKE_ESCAPE)
                    for column in (
                        Vulnerability.cve_id,
                        Vulnerability.description,
                        Vulnerability.kev_vendor_project,
                        Vulnerability.kev_product,
                    )
                )
            )
        )
    if f.is_kev is not None:
        stmt = stmt.where(Vulnerability.is_known_exploited.is_(f.is_kev))
    if f.min_cvss is not None:
        stmt = stmt.where(Vulnerability.cvss_score >= f.min_cvss)
    if f.max_cvss is not None:
        stmt = stmt.where(Vulnerability.cvss_score <= f.max_cvss)
    if f.has_cvss is True:
        stmt = stmt.where(Vulnerability.cvss_score.is_not(None))
    elif f.has_cvss is False:
        stmt = stmt.where(Vulnerability.cvss_score.is_(None))
    if f.published_after is not None:
        stmt = stmt.where(Vulnerability.published_at >= f.published_after)
    if f.published_before is not None:
        stmt = stmt.where(Vulnerability.published_at <= f.published_before)
    return stmt


def search_vulnerabilities(
    session: Session,
    filters: VulnerabilityFilters,
    sort: VulnerabilitySort,
    offset: int,
    limit: int,
) -> tuple[list[Vulnerability], int]:
    """Devuelve una página de resultados y el total que cumple los filtros."""
    total = session.scalar(_apply_filters(select(func.count(Vulnerability.id)), filters)) or 0
    stmt = (
        _apply_filters(select(Vulnerability), filters)
        .order_by(_SORT_COLUMNS[sort], Vulnerability.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.scalars(stmt)), total
