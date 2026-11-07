import time
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.core import security
from app.core.config import get_settings
from app.core.security import InvalidTokenError, decode_clerk_token
from app.db.session import get_db
from app.main import app
from app.models import User

# pk_test_ + base64("clerk.example.accounts.dev$")
PUBLISHABLE_KEY = "pk_test_Y2xlcmsuZXhhbXBsZS5hY2NvdW50cy5kZXYk"
ISSUER = "https://clerk.example.accounts.dev"
PUBLIC_URL = "https://gtip.example.com"


@pytest.fixture(scope="module")
def private_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def clerk(monkeypatch, private_key):
    monkeypatch.setenv("CLERK_PUBLISHABLE_KEY", PUBLISHABLE_KEY)
    monkeypatch.setenv("PUBLIC_URL", PUBLIC_URL)
    get_settings.cache_clear()
    fake = SimpleNamespace(
        get_signing_key_from_jwt=lambda _token: SimpleNamespace(key=private_key.public_key())
    )
    monkeypatch.setattr(security, "_jwks_client", lambda _issuer: fake)
    yield
    get_settings.cache_clear()


def make_token(private_key, **overrides):
    now = int(time.time())
    claims = {
        "sub": "user_abc12345",
        "iss": ISSUER,
        "iat": now,
        "exp": now + 60,
        "azp": PUBLIC_URL,
        **overrides,
    }
    claims = {key: value for key, value in claims.items() if value is not None}
    return jwt.encode(claims, private_key, algorithm="RS256")


def test_issuer_is_derived_from_publishable_key(clerk):
    assert get_settings().clerk_issuer_url == ISSUER


def test_not_configured_without_key(monkeypatch):
    monkeypatch.delenv("CLERK_PUBLISHABLE_KEY", raising=False)
    monkeypatch.delenv("CLERK_ISSUER", raising=False)
    get_settings.cache_clear()
    try:
        assert get_settings().clerk_issuer_url is None
        with pytest.raises(InvalidTokenError):
            decode_clerk_token("x.y.z")
    finally:
        get_settings.cache_clear()


def test_valid_token_returns_claims(clerk, private_key):
    claims = decode_clerk_token(make_token(private_key))
    assert claims["sub"] == "user_abc12345"


def test_localhost_dev_origin_is_accepted(clerk, private_key):
    token = make_token(private_key, azp="http://localhost:5173")
    assert decode_clerk_token(token)["sub"] == "user_abc12345"


@pytest.mark.parametrize(
    "overrides",
    [
        {"exp": int(time.time()) - 10},
        {"iss": "https://otro.example.com"},
        {"azp": "https://sitio-malicioso.example.com"},
        {"sub": None},
    ],
)
def test_invalid_tokens_are_rejected(clerk, private_key, overrides):
    with pytest.raises(InvalidTokenError):
        decode_clerk_token(make_token(private_key, **overrides))


def test_token_signed_with_another_key_is_rejected(clerk):
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(InvalidTokenError):
        decode_clerk_token(make_token(other))


def test_hs256_token_cannot_pass_as_clerk(clerk, private_key):
    forged = jwt.encode(
        {"sub": "user_x", "iss": ISSUER, "iat": int(time.time()), "exp": int(time.time()) + 60},
        "secreto",
        algorithm="HS256",
    )
    with pytest.raises(InvalidTokenError):
        decode_clerk_token(forged)


@pytest.fixture
def db_client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_first_clerk_request_creates_account_and_reuses_it(
    clerk, private_key, db_client, db_session
):
    token = make_token(private_key, email="ana@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    first = db_client.get("/api/v1/auth/me", headers=headers)
    assert first.status_code == 200
    assert first.json()["username"] == "ana"
    assert first.json()["auth_provider"] == "clerk"

    second = db_client.get("/api/v1/auth/me", headers=headers)
    assert second.json()["id"] == first.json()["id"]
    assert db_session.query(User).filter_by(provider_user_id="user_abc12345").count() == 1


def test_invalid_clerk_token_gets_401(clerk, private_key, db_client):
    token = make_token(private_key, iss="https://otro.example.com")
    response = db_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_disabled_clerk_user_gets_401(clerk, private_key, db_client, db_session):
    db_session.add(
        User(
            username="baneado",
            password_hash=None,
            auth_provider="clerk",
            provider_user_id="user_abc12345",
            is_active=False,
        )
    )
    db_session.commit()
    response = db_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {make_token(private_key)}"}
    )
    assert response.status_code == 401
