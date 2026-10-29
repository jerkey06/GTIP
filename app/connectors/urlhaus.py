import httpx
import csv
from typing import List, Dict, Any

class URLhausConnector:
    """Conector asíncrono para consumir IoCs maliciosos desde feeds públicos sin WAF."""

    def __init__(self):
        self.urlhaus_backup_url = "https://feodotracker.abuse.ch/downloads/ipblocklist.csv"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        self.timeout = 15.0

    async def fetch_recent_urls(self, limit: int = 50) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.get(self.urlhaus_backup_url, headers=self.headers)
                print(f"[DEBUG Feodo/URLhaus] Status Code: {response.status_code}")
                
                if response.status_code != 200:
                    return []

                # Filtrar comentarios y encabezados
                clean_lines = [
                    line.strip() for line in response.text.splitlines() 
                    if line.strip() and not line.strip().startswith('#')
                ]
                
                reader = csv.reader(clean_lines)
                parsed_items = []
                
                for row in reader:
                    # Formato Feodo: first_seen_utc, dst_ip, dst_port, c2_status, last_online, malware
                    if len(row) >= 6:
                        first_seen = row[0]
                        ip_val = row[1]
                        port_val = row[2]
                        status_val = row[3]
                        last_online = row[4]
                        malware_val = row[5] if len(row) > 5 else "botnet_c2"

                        # Ignorar la línea de encabezados si se coló
                        if ip_val == "dst_ip":
                            continue

                        parsed_items.append({
                            "value": f"http://{ip_val}:{port_val}",
                            "type": "url",
                            "source_name": "URLhaus/Feodo",
                            "threat_type": malware_val.strip('" ') if malware_val else "botnet_c2",
                            "confidence_score": 85.0 if status_val == "online" else 60.0,
                            "description": f"Botnet C2 Server ({malware_val}) | First Seen: {first_seen} | Status: {status_val}"
                        })

                        if len(parsed_items) >= limit:
                            break

                print(f"[DEBUG Feodo/URLhaus] Total procesados limpios: {len(parsed_items)}")
                return parsed_items

            except Exception as e:
                print(f"[DEBUG URLhaus EXCEPTION]: {type(e).__name__} - {str(e)}")
                return []