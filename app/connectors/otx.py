import httpx
from typing import List, Dict, Any
from app.core.config import settings

class OTXConnector:
    """Conector asíncrono para consultar pulsos de amenazas en AlienVault OTX."""

    def __init__(self):
        self.base_url = "https://otx.alienvault.com/api/v1/pulses/subscribed"
        self.headers = {
            "X-OTX-API-KEY": settings.OTX_API_KEY
        }
        self.timeout = 15.0

    async def fetch_recent_indicators(self, limit: int = 30) -> List[Dict[str, Any]]:
        if not settings.OTX_API_KEY:
            return []

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}?limit={limit}", headers=self.headers)
                if response.status_code != 200:
                    return []

                data = response.json()
                pulses = data.get("results", [])
                indicators = []

                for pulse in pulses:
                    pulse_name = pulse.get("name", "Unknown Pulse")
                    
                    # Recortar threat_type a máximo 95 caracteres para asegurar que quepa en VARCHAR(100)
                    safe_threat_type = pulse_name[:95] if pulse_name else "otx_pulse"
                    
                    for indicator in pulse.get("indicators", []):
                        indicator_val = indicator.get("indicator")
                        if not indicator_val:
                            continue

                        # Recortar description si la columna tuviera límite
                        desc = f"Pulse: {pulse_name} | Created: {indicator.get('created')}"
                        safe_desc = desc[:250]

                        indicators.append({
                            "value": str(indicator_val),
                            "type": str(indicator.get("type", "unknown")).lower(),
                            "source_name": "AlienVault OTX",
                            "threat_type": safe_threat_type,
                            "confidence_score": 75.0,
                            "description": safe_desc
                        })

                        if len(indicators) >= limit:
                            break

                    if len(indicators) >= limit:
                        break

                return indicators
            except Exception as e:
                print(f"[DEBUG OTX EXCEPTION]: {str(e)}")
                return []