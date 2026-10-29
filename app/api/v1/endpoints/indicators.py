from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.indicator import Indicator
from app.services.ioc_ingestion import sync_urlhaus_data
from app.connectors.abuseipdb import AbuseIPDBConnector
from app.connectors.otx import OTXConnector

router = APIRouter()
abuse_connector = AbuseIPDBConnector()
otx_connector = OTXConnector()

@router.post("/sync/urlhaus")
async def sync_urlhaus(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Ingiere URLs maliciosas recientes desde URLhaus/Feodo."""
    return await sync_urlhaus_data(db, limit=limit)

@router.get("/check-ip/{ip_address}")
async def check_ip_reputation(ip_address: str, db: AsyncSession = Depends(get_db)):
    """Consulta la reputación de una IP en AbuseIPDB y la guarda en la BDD."""
    result = await abuse_connector.check_ip(ip_address)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo obtener la reputación desde AbuseIPDB (Verifica que ABUSEIPDB_API_KEY esté en el .env)."
        )

    stmt = select(Indicator).where(Indicator.value == result["value"])
    existing = (await db.execute(stmt)).scalar_one_or_none()

    if existing:
        existing.confidence_score = result["confidence_score"]
        existing.description = result["description"]
    else:
        new_ioc = Indicator(
            value=result["value"],
            type=result["type"],
            source_name=result["source_name"],
            threat_type=result["threat_type"],
            confidence_score=result["confidence_score"],
            description=result["description"]
        )
        db.add(new_ioc)

    await db.commit()
    return result

@router.post("/sync/otx")
async def sync_otx_pulses(limit: int = 30, db: AsyncSession = Depends(get_db)):
    """Ingiere indicadores recientes desde los pulsos suscritos en AlienVault OTX."""
    indicators = await otx_connector.fetch_recent_indicators(limit=limit)
    if not indicators:
        return {
            "status": "warning",
            "message": "No se obtuvieron indicadores (Verifica que OTX_API_KEY esté configurada en el .env)",
            "total_fetched": 0,
            "new_indicators": 0
        }

    inserted = 0
    updated = 0

    for item in indicators:
        stmt = select(Indicator).where(Indicator.value == item["value"])
        existing = (await db.execute(stmt)).scalar_one_or_none()

        if existing:
            existing.confidence_score = item["confidence_score"]
            existing.description = item["description"]
            updated += 1
        else:
            new_ioc = Indicator(
                value=item["value"],
                type=item["type"],
                source_name=item["source_name"],
                threat_type=item["threat_type"],
                confidence_score=item["confidence_score"],
                description=item["description"]
            )
            db.add(new_ioc)
            inserted += 1

    await db.commit()

    return {
        "status": "success",
        "total_fetched": len(indicators),
        "new_indicators": inserted,
        "updated_indicators": updated
    }