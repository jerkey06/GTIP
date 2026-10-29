from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.db.session import AsyncSessionLocal
from app.services.ingestion import sync_cisa_kev_data
import logging

logger = logging.getLogger(__name__)

# Instancia del scheduler asíncrono
scheduler = AsyncIOScheduler()

async def scheduled_cisa_sync():
    """Tarea programada para sincronizar CISA KEV en segundo plano."""
    logger.info("Iniciando sincronización programada de CISA KEV...")
    async with AsyncSessionLocal() as db:
        try:
            result = await sync_cisa_kev_data(db)
            logger.info(f"Sincronización exitosa: {result}")
        except Exception as e:
            logger.error(f"Error en la sincronización programada: {str(e)}")

def start_scheduler():
    """Inicia el programador con un intervalo ejecutable (ej. cada 12 horas)."""
    # Ejecuta la sincronización automáticamente cada 12 horas
    scheduler.add_job(
        scheduled_cisa_sync,
        trigger="interval",
        hours=12,
        id="cisa_sync_job",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler iniciado correctamente.")

def stop_scheduler():
    """Detiene el programador al apagar la aplicación."""
    scheduler.shutdown()
    logger.info("Scheduler detenido.")