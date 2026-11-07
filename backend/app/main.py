import logging
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.v1 import (
    auth,
    dashboard,
    health,
    indicators,
    ingestions,
    search,
    sources,
    vulnerabilities,
)
from app.core.config import get_settings
from app.core.logging import configure_logging

log = logging.getLogger("gtip.api")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Con EMBEDDED_WORKER=true el worker de ingesta corre como hilo de la propia API."""
    if not get_settings().embedded_worker:
        yield
        return
    from app.ingestion.worker import run_forever

    stop = threading.Event()

    def run() -> None:
        try:
            run_forever(stop)
        except Exception:
            log.exception("El worker incrustado se detuvo por un error")

    thread = threading.Thread(target=run, name="gtip-worker", daemon=True)
    thread.start()
    log.info("Worker de ingesta incrustado en la API")
    try:
        yield
    finally:
        stop.set()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level, component="api")
    app = FastAPI(
        lifespan=lifespan,
        title="GTIP API",
        version=__version__,
        description="Global Threat Intelligence Platform: vulnerabilidades e indicadores "
        "de compromiso de fuentes públicas, normalizados y con su procedencia.",
        # La documentación interactiva no se expone en producción (ADD §12.4).
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    for module in (
        health,
        auth,
        dashboard,
        sources,
        vulnerabilities,
        indicators,
        ingestions,
        search,
    ):
        app.include_router(module.router, prefix="/api/v1")

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # Sin trazas ni detalles internos en la respuesta (ADD §11.4).
        log.exception("Error no controlado en %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})

    if settings.frontend_dist_dir:
        _mount_frontend(app, Path(settings.frontend_dist_dir))
    return app


def _mount_frontend(app: FastAPI, dist: Path) -> None:
    """Sirve el frontend compilado junto a la API (ADR-04), con rutas de la SPA."""
    index = dist / "index.html"
    if not index.is_file():
        log.warning("FRONTEND_DIST_DIR=%s no contiene index.html; no se sirve el frontend", dist)
        return
    if (dist / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")
    root = dist.resolve()

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str) -> FileResponse:
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = (root / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(root):
            return FileResponse(candidate)
        return FileResponse(index)


app = create_app()
