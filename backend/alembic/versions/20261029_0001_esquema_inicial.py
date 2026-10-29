"""Esquema inicial: fuentes, vulnerabilidades, indicadores, observaciones, ingestas y usuarios

Revision ID: 0001
Revises:
Create Date: 2026-10-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDICATOR_TYPES = ("ipv4", "ipv6", "domain", "url", "md5", "sha1", "sha256")
INGESTION_STATUSES = ("pending", "running", "completed", "partial", "failed")
TRIGGER_TYPES = ("manual", "scheduled")

# Catálogo inicial (ADD §7.1). Los provider_key son el contrato con los conectores.
INITIAL_SOURCES = [
    {
        "provider_key": "cisa_kev",
        "name": "CISA KEV",
        "description": "Catálogo de vulnerabilidades conocidas por estar explotadas.",
        "base_url": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
        "is_enabled": True,
    },
    {
        "provider_key": "nvd",
        "name": "NVD",
        "description": "National Vulnerability Database: detalles y puntuaciones CVSS de CVE.",
        "base_url": "https://nvd.nist.gov/developers/vulnerabilities",
        "is_enabled": True,
    },
    {
        "provider_key": "urlhaus",
        "name": "URLhaus",
        "description": "URLs relacionadas con la distribución de malware (abuse.ch).",
        "base_url": "https://urlhaus.abuse.ch/",
        "is_enabled": True,
    },
    {
        "provider_key": "abuseipdb",
        "name": "AbuseIPDB",
        "description": "Reputación de direcciones IP. Opcional: requiere clave de API.",
        "base_url": "https://www.abuseipdb.com/",
        "is_enabled": False,
    },
    {
        "provider_key": "otx",
        "name": "AlienVault OTX",
        "description": "Indicadores y contexto comunitario. Opcional: requiere clave de API.",
        "base_url": "https://otx.alienvault.com/",
        "is_enabled": False,
    },
]


def _check_in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade() -> None:
    sources = op.create_table(
        "sources",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("provider_key", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("base_url", sa.Text()),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("last_success_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_sources"),
        sa.UniqueConstraint("provider_key", name="uq_sources_provider_key"),
    )

    op.create_table(
        "vulnerabilities",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("cve_id", sa.String(32), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("cvss_score", sa.Numeric(3, 1)),
        sa.Column("cvss_version", sa.String(10)),
        sa.Column("cvss_vector", sa.Text()),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("modified_at", sa.DateTime(timezone=True)),
        sa.Column("is_known_exploited", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("kev_added_at", sa.Date()),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_vulnerabilities"),
        sa.UniqueConstraint("cve_id", name="uq_vulnerabilities_cve_id"),
    )
    op.create_index("ix_vulnerabilities_published_at", "vulnerabilities", ["published_at"])
    op.create_index("ix_vulnerabilities_modified_at", "vulnerabilities", ["modified_at"])
    op.create_index(
        "ix_vulnerabilities_is_known_exploited", "vulnerabilities", ["is_known_exploited"]
    )

    op.create_table(
        "indicators",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("indicator_type", sa.String(20), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("normalized_value", sa.Text(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True)),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_indicators"),
        sa.UniqueConstraint(
            "indicator_type",
            "normalized_value",
            name="uq_indicators_indicator_type_normalized_value",
        ),
        sa.CheckConstraint(
            _check_in("indicator_type", INDICATOR_TYPES), name=op.f("ck_indicators_indicator_type")
        ),
    )

    op.create_table(
        "observations",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("indicator_id", sa.BigInteger(), nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("external_id", sa.String(255)),
        sa.Column("first_seen_at", sa.DateTime(timezone=True)),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column(
            "observed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("reference_url", sa.Text()),
        sa.Column(
            "source_data",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_observations"),
        sa.ForeignKeyConstraint(
            ["indicator_id"],
            ["indicators.id"],
            name="fk_observations_indicator_id_indicators",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name="fk_observations_source_id_sources",
            ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_observations_indicator_id", "observations", ["indicator_id"])
    op.create_index("ix_observations_source_id", "observations", ["source_id"])
    op.create_index(
        "uq_observations_indicator_source_external",
        "observations",
        ["indicator_id", "source_id", "external_id"],
        unique=True,
        postgresql_where=sa.text("external_id IS NOT NULL"),
    )
    op.create_index(
        "uq_observations_indicator_source_no_external",
        "observations",
        ["indicator_id", "source_id"],
        unique=True,
        postgresql_where=sa.text("external_id IS NULL"),
    )

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("trigger_type", sa.String(20), nullable=False),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("records_processed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_updated", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_summary", sa.Text()),
        sa.PrimaryKeyConstraint("id", name="pk_ingestion_runs"),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name="fk_ingestion_runs_source_id_sources",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            _check_in("status", INGESTION_STATUSES), name=op.f("ck_ingestion_runs_ingestion_status")
        ),
        sa.CheckConstraint(
            _check_in("trigger_type", TRIGGER_TYPES), name=op.f("ck_ingestion_runs_trigger_type")
        ),
    )
    op.create_index("ix_ingestion_runs_source_id", "ingestion_runs", ["source_id"])
    op.create_index("ix_ingestion_runs_status", "ingestion_runs", ["status"])
    op.create_index("ix_ingestion_runs_started_at", "ingestion_runs", ["started_at"])

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )

    op.bulk_insert(sources, INITIAL_SOURCES)


def downgrade() -> None:
    op.drop_table("users")
    op.drop_table("ingestion_runs")
    op.drop_table("observations")
    op.drop_table("indicators")
    op.drop_table("vulnerabilities")
    op.drop_table("sources")
