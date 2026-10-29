from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, IdMixin


class Source(IdMixin, CreatedAtMixin, Base):
    """Proveedor de inteligencia. ``provider_key`` es su identificador interno estable."""

    __tablename__ = "sources"

    provider_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    base_url: Mapped[str | None] = mapped_column(Text)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
    # Estado técnico de la fuente, independiente de la validez de sus datos (ADD §10.1).
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
