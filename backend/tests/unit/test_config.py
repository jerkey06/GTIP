import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_development_allows_default_secret():
    settings = Settings(_env_file=None, app_env="development", app_secret_key="change-me")
    assert not settings.is_production


def test_production_rejects_default_secret():
    with pytest.raises(ValidationError, match="APP_SECRET_KEY"):
        Settings(_env_file=None, app_env="production", app_secret_key="change-me")


def test_production_rejects_short_secret():
    with pytest.raises(ValidationError, match="APP_SECRET_KEY"):
        Settings(_env_file=None, app_env="production", app_secret_key="corta")


def test_production_accepts_long_secret():
    settings = Settings(_env_file=None, app_env="production", app_secret_key="x" * 48)
    assert settings.is_production


def test_token_lifetime_must_be_positive():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, access_token_expire_minutes=0)
