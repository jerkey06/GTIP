from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DbSession
from app.api.v1.indicators import build_filters
from app.domain.records import CVE_ID_PATTERN
from app.repositories import indicators as indicators_repo
from app.repositories import vulnerabilities as vulns_repo
from app.repositories.vulnerabilities import VulnerabilityFilters, VulnerabilitySort
from app.schemas.indicators import IndicatorRead
from app.schemas.search import ExactMatch, SearchGroup, SearchResult
from app.schemas.vulnerabilities import VulnerabilityListItem

router = APIRouter(tags=["search"])

GROUP_SIZE = 5


@router.get("/search", response_model=SearchResult)
def search(
    db: DbSession,
    user: CurrentUser,
    q: Annotated[str, Query(min_length=1, max_length=2048)],
) -> SearchResult:
    """Búsqueda unificada de CVE e indicadores en los datos guardados (PRD §11.1)."""
    query = q.strip()
    upper = query.upper()
    if CVE_ID_PATTERN.match(upper):
        exact = vulns_repo.get_by_cve_id(db, upper)
        vulns, vulns_total = vulns_repo.search_vulnerabilities(
            db, VulnerabilityFilters(q=upper), VulnerabilitySort.PUBLISHED_DESC, 0, GROUP_SIZE
        )
        return SearchResult(
            query=query,
            kind="cve",
            indicator_type=None,
            exact_match=ExactMatch(kind="vulnerability", cve_id=upper) if exact else None,
            vulnerabilities=SearchGroup(
                items=[VulnerabilityListItem.model_validate(v) for v in vulns], total=vulns_total
            ),
            indicators=SearchGroup(items=[], total=0),
        )

    filters, detected, is_exact = build_filters(query, None)
    indicators, indicators_total = indicators_repo.search_indicators(db, filters, 0, GROUP_SIZE)
    vulns, vulns_total = vulns_repo.search_vulnerabilities(
        db, VulnerabilityFilters(q=query), VulnerabilitySort.PUBLISHED_DESC, 0, GROUP_SIZE
    )
    exact_match = None
    if is_exact and indicators_total == 1:
        exact_match = ExactMatch(kind="indicator", indicator_id=indicators[0].indicator.id)
    return SearchResult(
        query=query,
        kind=detected.value if detected else "text",
        indicator_type=detected,
        exact_match=exact_match,
        vulnerabilities=SearchGroup(
            items=[VulnerabilityListItem.model_validate(v) for v in vulns], total=vulns_total
        ),
        indicators=SearchGroup(
            items=[IndicatorRead.from_summary(s) for s in indicators], total=indicators_total
        ),
    )
