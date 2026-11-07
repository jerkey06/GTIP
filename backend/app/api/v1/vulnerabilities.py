from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DbSession, ReadUser
from app.domain.records import CVE_ID_PATTERN
from app.repositories import sources as sources_repo
from app.repositories import vulnerabilities as vulns_repo
from app.repositories.vulnerabilities import VulnerabilityFilters, VulnerabilitySort
from app.schemas.common import Page, Pagination, pagination
from app.schemas.vulnerabilities import Provenance, VulnerabilityDetail, VulnerabilityListItem

router = APIRouter(prefix="/vulnerabilities", tags=["vulnerabilities"])


@router.get("", response_model=Page[VulnerabilityListItem])
def list_vulnerabilities(
    db: DbSession,
    user: ReadUser,
    page: Annotated[Pagination, Depends(pagination)],
    q: Annotated[str | None, Query(max_length=200, description="CVE o texto")] = None,
    is_kev: Annotated[bool | None, Query(description="Solo (o sin) explotadas KEV")] = None,
    min_cvss: Annotated[Decimal | None, Query(ge=0, le=10)] = None,
    max_cvss: Annotated[Decimal | None, Query(ge=0, le=10)] = None,
    has_cvss: Annotated[bool | None, Query(description="Con o sin puntuación CVSS")] = None,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
    sort: VulnerabilitySort = VulnerabilitySort.PUBLISHED_DESC,
) -> Page[VulnerabilityListItem]:
    filters = VulnerabilityFilters(
        q=q.strip() if q and q.strip() else None,
        is_kev=is_kev,
        min_cvss=min_cvss,
        max_cvss=max_cvss,
        has_cvss=has_cvss,
        published_after=published_after,
        published_before=published_before,
    )
    items, total = vulns_repo.search_vulnerabilities(db, filters, sort, page.offset, page.page_size)
    return Page(
        items=[VulnerabilityListItem.model_validate(v) for v in items],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.get(
    "/{cve_id}",
    response_model=VulnerabilityDetail,
    responses={400: {"description": "CVE mal formada"}, 404: {"description": "No está en GTIP"}},
)
def get_vulnerability(cve_id: str, db: DbSession, user: ReadUser) -> VulnerabilityDetail:
    cve_id = cve_id.strip().upper()
    if not CVE_ID_PATTERN.match(cve_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Identificador CVE inválido")
    vuln = vulns_repo.get_by_cve_id(db, cve_id)
    if vuln is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{cve_id} no está en la base de datos")

    provenance = []
    contributed = {
        "cisa_kev": vuln.kev_added_at is not None or vuln.kev_vendor_project is not None,
        "nvd": vuln.nvd_references is not None
        or vuln.cvss_version is not None
        or vuln.modified_at is not None,
    }
    for provider_key, present in contributed.items():
        source = sources_repo.get_by_provider_key(db, provider_key)
        if present and source is not None:
            provenance.append(
                Provenance(
                    provider_key=provider_key,
                    name=source.name,
                    last_success_at=source.last_success_at,
                )
            )
    return VulnerabilityDetail.build(vuln, provenance)
