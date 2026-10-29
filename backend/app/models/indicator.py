from datetime import datetime

from sqlalchemy import DateTime, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, IdMixin
from app.domain.enums import IndicatorType
from app.models._types import str_enum


class Indicator(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "indicators"
    # Identidad lógica: tipo + valor normalizado (ADD §9.2). El índice único también
    # sirve para buscar por tipo y valor (PRD §9.7).
    __table_args__ = (UniqueConstraint("indicator_type", "normalized_value"),)

    indicator_type: Mapped[IndicatorType] = mapped_column(
        str_enum(IndicatorType, "indicator_type"), nullable=False
    )
    value: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_value: Mapped[str] = mapped_column(Text, nullable=False)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    observations: Mapped[list["Observation"]] = relationship(  # noqa: F821
        back_populates="indicator", passive_deletes=True
    )
