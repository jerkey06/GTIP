from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin
from app.domain.enums import IngestionStatus, TriggerType
from app.models._types import str_enum
from app.models.source import Source
from app.models.user import User


class IngestionRun(IdMixin, Base):
    """Una ejecución de ingesta de una fuente (ADD §8.3).

    También hace de solicitud de trabajo para el worker (ADD §10.1, ``ingestion_jobs``):
    la API o el planificador la crean en ``pending`` y el worker la reclama con
    ``FOR UPDATE SKIP LOCKED``. Así el historial muestra la ejecución desde que se pide.
    """

    __tablename__ = "ingestion_runs"
    __table_args__ = (
        # Como mucho una ejecución pendiente o en curso por fuente (ADD §6.5). La API
        # responde 409 si se pide otra.
        Index(
            "uq_ingestion_runs_active_source",
            "source_id",
            unique=True,
            postgresql_where=text("status IN ('pending', 'running')"),
        ),
    )

    source_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[IngestionStatus] = mapped_column(
        str_enum(IngestionStatus, "ingestion_status"), nullable=False, index=True
    )
    trigger_type: Mapped[TriggerType] = mapped_column(
        str_enum(TriggerType, "trigger_type"), nullable=False
    )
    requested_by_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL")
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_processed: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    records_created: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    records_updated: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    # Resumen sin secretos: nunca claves de API ni tokens (ADD §8.3).
    error_summary: Mapped[str | None] = mapped_column(Text)

    source: Mapped[Source] = relationship()
    requested_by: Mapped[User | None] = relationship()
