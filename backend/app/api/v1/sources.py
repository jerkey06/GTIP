from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DbSession, ReadUser
from app.core.config import get_settings
from app.schemas.sources import SourceRead
from app.services.sources import get_source_read, list_source_reads

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceRead])
def list_sources(db: DbSession, user: ReadUser) -> list[SourceRead]:
    """Fuentes integradas y su estado técnico, basado en sus ejecuciones (PRD §10.5)."""
    return list_source_reads(db, get_settings())


@router.get("/{source_id}", response_model=SourceRead, responses={404: {}})
def get_source(source_id: int, db: DbSession, user: ReadUser) -> SourceRead:
    source = get_source_read(db, get_settings(), source_id)
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La fuente no existe")
    return source
