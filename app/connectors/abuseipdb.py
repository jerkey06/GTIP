import httpx
from typing import Optional, Dict, Any
from app.core.config import settings

class AbuseIPDBConnector:
    """Conector asíncrono para verificar reputación de IPs en AbuseIPDB."""

    def __init__(self):
        self.base_url = "https://api.abuseipdb.com/api/v2/check"
        self.headers = {
            "Accept": "application/json",
            "Key": settings.ABUSEIPDB_API_KEY
        }
        self.timeout = 10.0

    async def check_ip(self, ip_address: str) -> Optional[Dict[str, Any]]:
        if not settings.ABUSEIPDB_API_KEY:
            return None

        params = {
            "ipAddress": ip_address,
            "maxAgeInDays": "90",
            "verbose": True
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.base_url, headers=self.headers, params=params)
            if response.status_code != 200:
                return None

            data = response.json().get("data", {})
            return {
                "value": data.get("ipAddress"),
                "type": "ip",
                "source_name": "AbuseIPDB",
                "threat_type": "suspicious_ip",
                "confidence_score": float(data.get("abuseConfidenceScore", 0)),
                "description": f"Domain: {data.get('domain')} | Total Reports: {data.get('totalReports')} | Country: {data.get('countryCode')}"
            }