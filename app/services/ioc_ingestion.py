from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.connectors.urlhaus import URLhausConnector
from app.models.indicator import Indicator

async def sync_urlhaus_data(db: AsyncSession, limit: int = 50) -> dict:
    connector = URLhausConnector()
    items = await connector.fetch_recent_urls(limit=limit)

    saved_count = 0
    updated_count = 0

    for item in items:
        stmt = select(Indicator).where(Indicator.value == item["value"])
        result = await db.execute(stmt)
        existing_ioc = result.scalar_one_or_none()

        if existing_ioc:
            existing_ioc.confidence_score = item["confidence_score"]
            existing_ioc.description = item["description"]
            updated_count += 1
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
            saved_count += 1

    await db.commit()
    return {
        "status": "success",
        "total_fetched": len(items),
        "new_indicators": saved_count,
        "updated_indicators": updated_count
    }