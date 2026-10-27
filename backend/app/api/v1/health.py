from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness: el proceso está en ejecución. La comprobación de PostgreSQL llega en semana 2."""
    return {"status": "ok"}
