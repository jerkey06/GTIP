"""Campos KEV y referencias NVD; las ejecuciones de ingesta pasan a ser también solicitudes

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("vulnerabilities", sa.Column("kev_short_description", sa.Text()))
    op.add_column("vulnerabilities", sa.Column("kev_vendor_project", sa.String(255)))
    op.add_column("vulnerabilities", sa.Column("kev_product", sa.String(255)))
    op.add_column("vulnerabilities", sa.Column("kev_vulnerability_name", sa.Text()))
    op.add_column("vulnerabilities", sa.Column("kev_required_action", sa.Text()))
    op.add_column("vulnerabilities", sa.Column("kev_due_date", sa.Date()))
    op.add_column("vulnerabilities", sa.Column("nvd_references", postgresql.JSONB()))

    # Ninguna ejecución anterior puede seguir viva: el worker nuevo no las conoce.
    op.execute(
        "UPDATE ingestion_runs SET status = 'failed', finished_at = now(), "
        "error_summary = 'Interrumpida por una actualización del esquema' "
        "WHERE status IN ('pending', 'running')"
    )

    op.add_column(
        "ingestion_runs",
        sa.Column("requested_by_id", sa.BigInteger()),
    )
    op.create_foreign_key(
        "fk_ingestion_runs_requested_by_id_users",
        "ingestion_runs",
        "users",
        ["requested_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column(
        "ingestion_runs",
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.execute("UPDATE ingestion_runs SET requested_at = started_at")
    op.create_index("ix_ingestion_runs_requested_at", "ingestion_runs", ["requested_at"])
    op.add_column("ingestion_runs", sa.Column("claimed_at", sa.DateTime(timezone=True)))
    op.execute("UPDATE ingestion_runs SET claimed_at = started_at")
    # Una solicitud pendiente todavía no ha empezado.
    op.alter_column("ingestion_runs", "started_at", nullable=True, server_default=None)
    op.create_index(
        "uq_ingestion_runs_active_source",
        "ingestion_runs",
        ["source_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'running')"),
    )


def downgrade() -> None:
    op.drop_index("uq_ingestion_runs_active_source", table_name="ingestion_runs")
    op.execute("DELETE FROM ingestion_runs WHERE started_at IS NULL")
    op.alter_column("ingestion_runs", "started_at", nullable=False, server_default=sa.func.now())
    op.drop_column("ingestion_runs", "claimed_at")
    op.drop_index("ix_ingestion_runs_requested_at", table_name="ingestion_runs")
    op.drop_column("ingestion_runs", "requested_at")
    op.drop_constraint(
        "fk_ingestion_runs_requested_by_id_users", "ingestion_runs", type_="foreignkey"
    )
    op.drop_column("ingestion_runs", "requested_by_id")

    op.drop_column("vulnerabilities", "nvd_references")
    op.drop_column("vulnerabilities", "kev_due_date")
    op.drop_column("vulnerabilities", "kev_required_action")
    op.drop_column("vulnerabilities", "kev_vulnerability_name")
    op.drop_column("vulnerabilities", "kev_product")
    op.drop_column("vulnerabilities", "kev_vendor_project")
    op.drop_column("vulnerabilities", "kev_short_description")
