import httpx
from typing import List
from app.core.config import settings
from app.schemas.vulnerability import CISA_KEV_Item

class CISA_KEVConnector:
    """Conector asíncrono para la API/Feed público de CISA KEV."""
    
    def __init__(self):
        self.url = settings.CISA_KEV_URL
        self.timeout = 15.0  # Timeout de 15 segundos para la petición HTTP

    async def fetch_vulnerabilities(self) -> List[CISA_KEV_Item]:
        """Descarga el catálogo JSON de CISA KEV y retorna los registros validados con Pydantic."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.url)
            response.raise_for_status()
            
            data = response.json()
            raw_vulnerabilities = data.get("vulnerabilities", [])
            
            validated_vulnerabilities = [
                CISA_KEV_Item(**item) for item in raw_vulnerabilities
            ]
            
            return validated_vulnerabilities