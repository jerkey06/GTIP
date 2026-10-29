import httpx
from typing import Optional, Dict, Any

class NVDConnector:
    """Conector asíncrono para consultar detalles de vulnerabilidades en la API v2 de NVD."""
    
    def __init__(self):
        self.base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.timeout = 10.0

    async def fetch_cve_detail(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """Consulta una vulnerabilidad específica por su CVE ID."""
        params = {"cveId": cve_id}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.base_url, params=params)
            if response.status_code != 200:
                return None
            
            data = response.json()
            vulnerabilities = data.get("vulnerabilities", [])
            if not vulnerabilities:
                return None
            
            cve_data = vulnerabilities[0].get("cve", {})
            
            # Extraer descripción en inglés
            descriptions = cve_data.get("descriptions", [])
            description = next((d.get("value") for d in descriptions if d.get("lang") == "en"), "")
            
            # Extraer métricas CVSS v3.1 o v3.0
            metrics = cve_data.get("metrics", {})
            cvss_score = None
            cvss_vector = None
            
            cvss_v31 = metrics.get("cvssMetricV31", [])
            if cvss_v31:
                cvss_data = cvss_v31[0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore")
                cvss_vector = cvss_data.get("vectorString")
            else:
                cvss_v30 = metrics.get("cvssMetricV30", [])
                if cvss_v30:
                    cvss_data = cvss_v30[0].get("cvssData", {})
                    cvss_score = cvss_data.get("baseScore")
                    cvss_vector = cvss_data.get("vectorString")
            
            return {
                "cve_id": cve_id,
                "description": description,
                "cvss_score": cvss_score,
                "cvss_vector": cvss_vector
            }