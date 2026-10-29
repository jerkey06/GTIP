"""Importa todos los modelos para que ``Base.metadata`` los conozca (Alembic los necesita)."""

from app.models.indicator import Indicator
from app.models.ingestion_run import IngestionRun
from app.models.observation import Observation
from app.models.source import Source
from app.models.user import User
from app.models.vulnerability import Vulnerability

__all__ = ["Indicator", "IngestionRun", "Observation", "Source", "User", "Vulnerability"]
