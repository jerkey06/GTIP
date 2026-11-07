"""Cuentas creadas con Google o GitHub: correo, proveedor y contraseña opcional

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=True)
    op.add_column("users", sa.Column("email", sa.String(320)))
    op.add_column(
        "users",
        sa.Column("auth_provider", sa.String(16), server_default="password", nullable=False),
    )
    op.add_column("users", sa.Column("provider_user_id", sa.String(255)))
    op.create_unique_constraint(
        "uq_users_provider_identity", "users", ["auth_provider", "provider_user_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_users_provider_identity", "users", type_="unique")
    op.drop_column("users", "provider_user_id")
    op.drop_column("users", "auth_provider")
    op.drop_column("users", "email")
    # Las cuentas sociales no tienen contraseña: se eliminan para poder volver a NOT NULL.
    op.execute("DELETE FROM users WHERE password_hash IS NULL")
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=False)
