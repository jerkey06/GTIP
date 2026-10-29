from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin
from app.domain.enums import IngestionStatus, TriggerType
from app.models._types import str_enum
from app.models.source import Source


class IngestionRun(IdMixin, Base):
    """Una ejecución de ingesta de una fuente (ADD §8.3)."""

    __tablename__ = "ingestion_runs"

    source_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[IngestionStatus] = mapped_column(
        str_enum(IngestionStatus, "ingestion_status"), nullable=False, index=True
    )
    trigger_type: Mapped[TriggerType] = mapped_column(
        str_enum(TriggerType, "trigger_type"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_processed: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    records_created: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    records_updated: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    # Resumen sin secretos: nunca claves de API ni tokens (ADD §8.3).
    error_summary: Mapped[str | None] = mapped_column(Text)

    source: Mapped[Source] = relationship()
