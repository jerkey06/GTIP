import pytest
from pydantic import ValidationError

from app.domain.records import VulnerabilityRecord


def test_cve_id_is_normalized():
    assert VulnerabilityRecord(cve_id=" cve-2024-12345 ").cve_id == "CVE-2024-12345"


@pytest.mark.parametrize("cve_id", ["", "CVE-24-1", "2024-1234", "CVE-2024-12"])
def test_invalid_cve_id_is_rejected(cve_id):
    with pytest.raises(ValidationError):
        VulnerabilityRecord(cve_id=cve_id)


def test_cvss_score_out_of_range_is_rejected():
    with pytest.raises(ValidationError):
        VulnerabilityRecord(cve_id="CVE-2024-0001", cvss_score=11)


def test_missing_kev_flag_means_unknown():
    assert VulnerabilityRecord(cve_id="CVE-2024-0001").is_known_exploited is None
