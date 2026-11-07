from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DbSession, ReadUser
from app.domain.enums import IndicatorType
from app.domain.indicators import InvalidIndicatorError, detect_type, normalize
from app.repositories import indicators as indicators_repo
from app.repositories.indicators import IndicatorFilters
from app.schemas.common import Pagination, SourceRef, pagination
from app.schemas.indicators import IndicatorRead, IndicatorSearchPage, ObservationRead

router = APIRouter(prefix="/indicators", tags=["indicators"])


def build_filters(
    value: str | None, indicator_type: IndicatorType | None, source_id: int | None = None
) -> tuple[IndicatorFilters, IndicatorType | None, bool]:
    """Traduce la búsqueda del usuario a filtros. Lanza 422 si el valor no encaja con el tipo.

    Un valor que es un indicador completo se busca por coincidencia exacta de su valor
    normalizado; si no se reconoce, por coincidencia parcial (PRD §10.3).
    """
    value = value.strip() if value else None
    if not value:
        return IndicatorFilters(indicator_type=indicator_type, source_id=source_id), None, False

    detected = indicator_type or detect_type(value)
    if detected is None:
        return IndicatorFilters(contains=value, source_id=source_id), None, False
    try:
        normalized = normalize(detected, value)
    except InvalidIndicatorError as exc:
        if indicator_type is None:
            return IndicatorFilters(contains=value, source_id=source_id), None, False
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from None
    filters = IndicatorFilters(
        indicator_type=detected, normalized_value=normalized, source_id=source_id
    )
    return filters, detected, True


@router.get("", response_model=IndicatorSearchPage)
def search_indicators(
    db: DbSession,
    user: ReadUser,
    page: Annotated[Pagination, Depends(pagination)],
    value: Annotated[
        str | None, Query(max_length=2048, description="IP, dominio, URL o hash")
    ] = None,
    indicator_type: Annotated[IndicatorType | None, Query(alias="type")] = None,
    source_id: Annotated[int | None, Query(gt=0)] = None,
) -> IndicatorSearchPage:
    """Busca en los datos guardados. Nunca consulta a proveedores externos (PRD §10.3)."""
    filters, detected, exact = build_filters(value, indicator_type, source_id)
    items, total = indicators_repo.search_indicators(db, filters, page.offset, page.page_size)
    return IndicatorSearchPage(
        items=[IndicatorRead.from_summary(s) for s in items],
        total=total,
        page=page.page,
        page_size=page.page_size,
        detected_type=detected,
        exact=exact,
    )


@router.get("/{indicator_id}", response_model=IndicatorRead, responses={404: {}})
def get_indicator(indicator_id: int, db: DbSession, user: ReadUser) -> IndicatorRead:
    summary = indicators_repo.get_summary(db, indicator_id)
    if summary is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Este indicador no existe en GTIP")
    return IndicatorRead.from_summary(summary)


@router.get(
    "/{indicator_id}/observations", response_model=list[ObservationRead], responses={404: {}}
)
def list_observations(indicator_id: int, db: DbSession, user: ReadUser) -> list[ObservationRead]:
    if indicators_repo.get_by_id(db, indicator_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Este indicador no existe en GTIP")
    return [
        ObservationRead(
            id=o.id,
            source=SourceRef(
                id=o.source.id, provider_key=o.source.provider_key, name=o.source.name
            ),
            external_id=o.external_id,
            first_seen_at=o.first_seen_at,
            last_seen_at=o.last_seen_at,
            observed_at=o.observed_at,
            reference_url=o.reference_url,
            source_data=o.source_data,
        )
        for o in indicators_repo.list_observations(db, indicator_id)
    ]
