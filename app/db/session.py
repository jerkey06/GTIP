from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Motor asíncrono para SQLAlchemy 2
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Creador de sesiones asíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """Inyector de dependencia para obtener la sesión de BDD en cada endpoint."""
    async with AsyncSessionLocal() as session:
        yield session