from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, IdMixin


class User(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("auth_provider", "provider_user_id", name="uq_users_provider_identity"),
    )

    # Se guarda en minúsculas para que "Admin" y "admin" sean la misma cuenta.
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    # Hash Argon2id; la contraseña en claro nunca se almacena (ADD §12.2).
    # Es NULL en cuentas creadas con Google o GitHub: no pueden entrar con contraseña.
    password_hash: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320))
    # "password", "google" o "github", y el identificador estable del usuario en ese proveedor.
    auth_provider: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="password"
    )
    provider_user_id: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
