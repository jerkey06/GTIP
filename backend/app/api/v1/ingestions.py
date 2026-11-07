from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.api.dependencies import CurrentUser, DbSession
from app.core.config import get_settings
from app.domain.enums import IngestionStatus, TriggerType
from app.repositories import ingestion_runs
from app.repositories import sources as sources_repo
from app.repositories.ingestion_runs import ActiveRunExistsError, RunFilters
from app.schemas.common import Page, Pagination, pagination
from app.schemas.ingestions import IngestionRequest, IngestionRunRead
from app.services.sources import disabled_reason

router = APIRouter(prefix="/ingestions", tags=["ingestions"])


@router.post(
    "",
    response_model=IngestionRunRead,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        404: {"description": "La fuente no existe"},
        409: {"description": "Fuente deshabilitada o con una ingesta activa"},
    },
)
def request_ingestion(
    body: IngestionRequest, db: DbSession, user: CurrentUser
) -> IngestionRunRead | JSONResponse:
    """Solicita una ingesta manual. La ejecuta el worker en segundo plano (ADD §8.2)."""
    source = sources_repo.get_by_id(db, body.source_id)
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La fuente no existe")
    reason = disabled_reason(source, get_settings())
    if reason:
        raise HTTPException(status.HTTP_409_CONFLICT, f"La fuente no está habilitada: {reason}")
    try:
        run = ingestion_runs.request_run(db, source, TriggerType.MANUAL, requested_by=user)
    except ActiveRunExistsError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Ya hay una ingesta pendiente o en ejecución para esta fuente",
                "active_run_id": exc.active_run.id if exc.active_run else None,
            },
        )
    db.commit()
    return IngestionRunRead.model_validate(ingestion_runs.get_run(db, run.id))


@router.get("", response_model=Page[IngestionRunRead])
def list_ingestions(
    db: DbSession,
    user: CurrentUser,
    page: Annotated[Pagination, Depends(pagination)],
    source_id: Annotated[int | None, Query(gt=0)] = None,
    status_: Annotated[IngestionStatus | None, Query(alias="status")] = None,
    trigger_type: TriggerType | None = None,
    requested_after: datetime | None = None,
    requested_before: datetime | None = None,
) -> Page[IngestionRunRead]:
    filters = RunFilters(
        source_id=source_id,
        status=status_,
        trigger_type=trigger_type,
        requested_after=requested_after,
        requested_before=requested_before,
    )
    runs, total = ingestion_runs.list_runs(db, filters, page.offset, page.page_size)
    return Page(
        items=[IngestionRunRead.model_validate(r) for r in runs],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.get("/{run_id}", response_model=IngestionRunRead, responses={404: {}})
def get_ingestion(run_id: int, db: DbSession, user: CurrentUser) -> IngestionRunRead:
    run = ingestion_runs.get_run(db, run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La ejecución no existe")
    return IngestionRunRead.model_validate(run)
