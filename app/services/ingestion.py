from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.connectors.cisa_kev import CISA_KEVConnector
from app.models.vulnerability import Vulnerability
from app.schemas.vulnerability_query import PaginatedVulnerabilitiesResponse, VulnerabilityResponse


async def sync_cisa_kev_data(db: AsyncSession) -> dict:
    """
    Descarga vulnerabilidades desde CISA KEV y las guarda o actualiza en la base de datos de forma idempotente.
    """
    connector = CISA_KEVConnector()
    items = await connector.fetch_vulnerabilities()
    
    saved_count = 0
    updated_count = 0

    for item in items:
        stmt = select(Vulnerability).where(Vulnerability.cve_id == item.cveID)
        result = await db.execute(stmt)
        existing_vuln = result.scalar_one_or_none()

        if existing_vuln:
            existing_vuln.description = item.shortDescription
            existing_vuln.is_kev = True
            existing_vuln.kev_added_at = item.dateAdded
            updated_count += 1
        else:
            new_vuln = Vulnerability(
                cve_id=item.cveID,
                description=f"[{item.vendorProject} - {item.product}] {item.shortDescription}",
                is_kev=True,
                kev_added_at=item.dateAdded
            )
            db.add(new_vuln)
            saved_count += 1

    await db.commit()
    return {
        "status": "success",
        "total_fetched": len(items),
        "new_records": saved_count,
        "updated_records": updated_count
    }


async def get_filtered_vulnerabilities(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    is_kev: Optional[bool] = None,
    min_cvss: Optional[float] = None
) -> PaginatedVulnerabilitiesResponse:
    """
    Obtiene vulnerabilidades de la base de datos con filtros y paginación.
    """
    query = select(Vulnerability)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Vulnerability.cve_id.ilike(search_pattern)) | 
            (Vulnerability.description.ilike(search_pattern))
        )

    if is_kev is not None:
        query = query.where(Vulnerability.is_kev == is_kev)

    if min_cvss is not None:
        query = query.where(Vulnerability.cvss_score >= min_cvss)

    total_stmt = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_stmt)).scalar() or 0

    offset = (page - 1) * size
    query = query.order_by(Vulnerability.created_at.desc()).offset(offset).limit(size)

    result = await db.execute(query)
    vulnerabilities = result.scalars().all()

    pages = (total + size - 1) // size if total > 0 else 0

    return PaginatedVulnerabilitiesResponse(
        total=total,
        page=page,
        size=size,
        pages=pages,
        items=[VulnerabilityResponse.model_validate(v) for v in vulnerabilities]
    )