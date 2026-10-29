from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

import app.models  # noqa: F401
from app.db.base import Base


def test_migrations_match_models(pg_engine):
    """Si falla, alguien cambió un modelo sin crear la migración correspondiente."""
    with pg_engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        diff = compare_metadata(context, Base.metadata)
    assert diff == []
