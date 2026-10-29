from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.connectors.cisa_kev import CISA_KEVConnector
from app.connectors.nvd import NVDConnector
from app.schemas.vulnerability import CISA_KEV_Item
from app.schemas.vulnerability_query import PaginatedVulnerabilitiesResponse
from app.services.ingestion import sync_cisa_kev_data, get_filtered_vulnerabilities
from app.models.vulnerability import Vulnerability

# 1. Definición del router PRIMERO para que esté disponible en los decoradores
router = APIRouter()

cisa_connector = CISA_KEVConnector()
nvd_connector = NVDConnector()

# 2. Endpoint para consulta paginada y filtros
@router.get("", response_model=PaginatedVulnerabilitiesResponse)
async def list_vulnerabilities(
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    is_kev: Optional[bool] = None,
    min_cvss: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    """Obtiene el listado paginado de vulnerabilidades con filtros opcionales."""
    return await get_filtered_vulnerabilities(
        db=db,
        page=page,
        size=size,
        search=search,
        is_kev=is_kev,
        min_cvss=min_cvss
    )

# 3. Endpoint de prueba en vivo CISA
@router.get("/cisa-test", response_model=List[CISA_KEV_Item])
async def get_cisa_vulnerabilities_live():
    """Consulta en tiempo real el catálogo de CISA KEV (Prueba sin BDD)."""
    try:
        vulnerabilities = await cisa_connector.fetch_vulnerabilities()
        return vulnerabilities[:20]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al obtener datos de CISA KEV: {str(e)}"
        )

# 4. Endpoint para sincronización con CISA
@router.post("/sync/cisa", status_code=status.HTTP_200_OK)
async def sync_cisa_kev(db: AsyncSession = Depends(get_db)):
    """Sincroniza e ingiere las vulnerabilidades del catálogo CISA KEV en la BDD PostgreSQL."""
    try:
        result = await sync_cisa_kev_data(db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en la sincronización con la BDD: {str(e)}"
        )

# 5. Endpoint para enriquecer con NVD
@router.post("/enrich/{cve_id}")
async def enrich_vulnerability_with_nvd(cve_id: str, db: AsyncSession = Depends(get_db)):
    """Enriquece los datos de una vulnerabilidad guardada en PostgreSQL consultando la API de NVD."""
    stmt = select(Vulnerability).where(Vulnerability.cve_id == cve_id)
    result = await db.execute(stmt)
    vuln = result.scalar_one_or_none()
    
    if not vuln:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La vulnerabilidad {cve_id} no existe en la BDD. Ejecuta primero /sync/cisa."
        )
    
    nvd_data = await nvd_connector.fetch_cve_detail(cve_id)
    if not nvd_data:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudieron obtener datos desde NVD para {cve_id}."
        )
    
    if nvd_data.get("cvss_score") is not None:
        vuln.cvss_score = nvd_data["cvss_score"]
    if nvd_data.get("cvss_vector"):
        vuln.cvss_vector = nvd_data["cvss_vector"]
    if nvd_data.get("description"):
        vuln.description = nvd_data["description"]
        
    await db.commit()
    await db.refresh(vuln)
    
    return {
        "status": "enriched",
        "cve_id": vuln.cve_id,
        "cvss_score": vuln.cvss_score,
        "cvss_vector": vuln.cvss_vector,
        "description": vuln.description
    }