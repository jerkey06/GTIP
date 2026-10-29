"""Fixtures compartidas.

Las pruebas que usan ``db_session`` necesitan PostgreSQL y se saltan si no está
definida TEST_DATABASE_URL. Debe ser una base de datos SOLO para pruebas: la
migración se deshace y se vuelve a aplicar al empezar y al terminar (ADD §16.2).
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parents[1]

# Clave fija y larga solo para pruebas; se define antes de que get_settings() se cachee.
os.environ["APP_SECRET_KEY"] = "clave-de-pruebas-" + "x" * 40


def _alembic_config(url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


class _TestSettings(BaseSettings):
    """Lee TEST_DATABASE_URL del entorno o del mismo .env que usa la aplicación."""

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    test_database_url: str | None = None


@pytest.fixture(scope="session")
def pg_engine() -> Iterator[Engine]:
    url = _TestSettings().test_database_url
    if not url:
        pytest.skip("TEST_DATABASE_URL no está definida: se omiten las pruebas con PostgreSQL")

    config = _alembic_config(url)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    engine = create_engine(url)
    yield engine
    engine.dispose()
    command.downgrade(config, "base")


@pytest.fixture
def db_session(pg_engine: Engine) -> Iterator[Session]:
    """Sesión dentro de una transacción que se deshace al final de cada prueba.

    Los ``commit()`` del código bajo prueba solo cierran un SAVEPOINT.
    """
    connection = pg_engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    )
    yield session
    session.close()
    transaction.rollback()
    connection.close()
