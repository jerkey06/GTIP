from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, IdMixin


class User(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "users"

    # Se guarda en minúsculas para que "Admin" y "admin" sean la misma cuenta.
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    # Hash Argon2id; la contraseña en claro nunca se almacena (ADD §12.2).
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
