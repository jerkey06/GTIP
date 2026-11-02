from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import __version__
from app.api.dependencies import DbSession
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness: el proceso está en ejecución (ADD §15.2)."""
    return {"status": "ok"}


@router.get("/health/ready")
def ready(db: DbSession, response: Response) -> dict[str, str]:
    """Readiness: la API puede atender peticiones porque PostgreSQL responde.

    Las fuentes externas no cuentan: su caída no deja GTIP inutilizable (ADD §15.2).
    """
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except SQLAlchemyError:
        database = "error"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ok" if database == "ok" else "degraded",
        "database": database,
        "version": __version__,
        "environment": get_settings().app_env,
    }
