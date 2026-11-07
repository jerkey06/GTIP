from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models import Vulnerability


class VulnerabilityListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cve_id: str
    description: str | None
    kev_short_description: str | None
    # Ausente = la fuente no ha publicado puntuación; nunca 0 (PRD §9.2).
    cvss_score: float | None
    cvss_version: str | None
    published_at: datetime | None
    modified_at: datetime | None
    is_known_exploited: bool
    kev_added_at: date | None
    created_at: datetime


class KevDetails(BaseModel):
    added_at: date | None
    vendor_project: str | None
    product: str | None
    vulnerability_name: str | None
    short_description: str | None
    required_action: str | None
    due_date: date | None


class Reference(BaseModel):
    url: str
    source: str | None = None
    tags: list[str] = []


class Provenance(BaseModel):
    """Fuente que aportó datos de la CVE y cuándo la sincronizó GTIP por última vez."""

    provider_key: str
    name: str
    last_success_at: datetime | None


class VulnerabilityDetail(VulnerabilityListItem):
    cvss_vector: str | None
    updated_at: datetime
    kev: KevDetails | None
    references: list[Reference]
    provenance: list[Provenance]

    @classmethod
    def build(cls, vuln: Vulnerability, provenance: list[Provenance]) -> "VulnerabilityDetail":
        kev = None
        if vuln.is_known_exploited or vuln.kev_added_at:
            kev = KevDetails(
                added_at=vuln.kev_added_at,
                vendor_project=vuln.kev_vendor_project,
                product=vuln.kev_product,
                vulnerability_name=vuln.kev_vulnerability_name,
                short_description=vuln.kev_short_description,
                required_action=vuln.kev_required_action,
                due_date=vuln.kev_due_date,
            )
        return cls(
            **VulnerabilityListItem.model_validate(vuln).model_dump(),
            cvss_vector=vuln.cvss_vector,
            updated_at=vuln.updated_at,
            kev=kev,
            references=[Reference.model_validate(r) for r in (vuln.nvd_references or [])],
            provenance=provenance,
        )
