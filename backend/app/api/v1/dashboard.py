from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DbSession
from app.core.config import get_settings
from app.schemas.dashboard import Dashboard
from app.services.dashboard import build_dashboard

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=Dashboard)
def dashboard(db: DbSession, user: CurrentUser) -> Dashboard:
    """Estadísticas y actividad reciente, calculadas de los datos guardados (PRD §10.1)."""
    return build_dashboard(db, get_settings())
