import pytest
import respx
from httpx import Response
from app.connectors.cisa_kev import CISA_KEVConnector
from app.core.config import settings

@pytest.mark.asyncio
async def test_fetch_vulnerabilities_success():
    # Creamos una respuesta ficticia simulando la API de CISA
    mock_payload = {
        "vulnerabilities": [
            {
                "cveID": "CVE-2026-0001",
                "vendorProject": "Test Vendor",
                "product": "Test Product",
                "vulnerabilityName": "Test Vulnerability",
                "dateAdded": "2026-10-28",
                "shortDescription": "Description test",
                "requiredAction": "Update immediately",
                "dueDate": "2026-11-10",
                "knownRansomwareCampaignUse": "Unknown"
            }
        ]
    }

    # Interceptamos la petición HTTP a la URL de CISA
    with respx.mock:
        respx.get(settings.CISA_KEV_URL).mock(
            return_value=Response(200, json=mock_payload)
        )

        connector = CISA_KEVConnector()
        results = await connector.fetch_vulnerabilities()

        # Verificaciones
        assert len(results) == 1
        assert results[0].cveID == "CVE-2026-0001"
        assert results[0].vendorProject == "Test Vendor"