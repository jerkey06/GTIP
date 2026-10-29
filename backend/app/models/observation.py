from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin
from app.models.indicator import Indicator
from app.models.source import Source


class Observation(IdMixin, Base):
    """Evidencia que una fuente aporta sobre un indicador, con su procedencia."""

    __tablename__ = "observations"
    __table_args__ = (
        # Sin duplicados cuando la fuente da un identificador externo estable (ADD §9.2).
        Index(
            "uq_observations_indicator_source_external",
            "indicator_id",
            "source_id",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
        # Sin identificador externo: una sola observación por indicador y fuente, para
        # que repetir una ingesta no la duplique (ADD §13.3).
        Index(
            "uq_observations_indicator_source_no_external",
            "indicator_id",
            "source_id",
            unique=True,
            postgresql_where=text("external_id IS NULL"),
        ),
    )

    indicator_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("indicators.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    external_id: Mapped[str | None] = mapped_column(String(255))
    # Fechas que reporta el proveedor...
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # ...y fecha en que GTIP lo obtuvo (ADD §9.3).
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reference_url: Mapped[str | None] = mapped_column(Text)
    source_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    indicator: Mapped[Indicator] = relationship(back_populates="observations")
    source: Mapped[Source] = relationship()
