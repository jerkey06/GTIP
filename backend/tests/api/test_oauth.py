from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import get_db
from app.main import app
from app.models import User
from app.services import oauth


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("PUBLIC_URL", "https://gtip.example.com")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "google-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "google-secret")
    monkeypatch.setenv("GITHUB_CLIENT_ID", "github-id")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "github-secret")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client():
    return TestClient(app, follow_redirects=False)


@pytest.fixture
def db_client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app, follow_redirects=False)
    app.dependency_overrides.clear()


def test_providers_reports_only_configured_ones(client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")
    monkeypatch.delenv("GITHUB_CLIENT_ID", raising=False)
    monkeypatch.delenv("GITHUB_CLIENT_SECRET", raising=False)
    get_settings.cache_clear()
    try:
        assert client.get("/api/v1/auth/providers").json() == {"google": True, "github": False}
    finally:
        get_settings.cache_clear()


def test_login_redirects_to_provider_and_sets_state_cookie(client, configured):
    response = client.get("/api/v1/auth/oauth/github/login")
    assert response.status_code == 302
    location = urlparse(response.headers["location"])
    query = parse_qs(location.query)
    assert location.netloc == "github.com"
    assert query["client_id"] == ["github-id"]
    assert query["redirect_uri"] == ["https://gtip.example.com/api/v1/auth/oauth/github/callback"]
    assert query["state"] == [response.cookies["gtip_oauth_state"]]
    assert "httponly" in response.headers["set-cookie"].lower()


def test_unconfigured_provider_goes_back_to_login(client, monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    get_settings.cache_clear()
    try:
        response = client.get("/api/v1/auth/oauth/google/login")
    finally:
        get_settings.cache_clear()
    assert response.status_code == 302
    assert response.headers["location"] == "/login?error=oauth_not_configured"


def test_unknown_provider_is_404(client):
    assert client.get("/api/v1/auth/oauth/facebook/login").status_code == 404


def test_callback_rejects_state_mismatch(client, configured):
    client.cookies.set("gtip_oauth_state", "uno", path="/api/v1/auth/oauth")
    response = client.get("/api/v1/auth/oauth/google/callback?code=abc&state=otro")
    assert response.headers["location"] == "/login?error=oauth_state"


def test_callback_without_cookie_is_rejected(client, configured):
    response = client.get("/api/v1/auth/oauth/google/callback?code=abc&state=x")
    assert response.headers["location"] == "/login?error=oauth_state"


def test_callback_reports_provider_denial(client, configured):
    response = client.get("/api/v1/auth/oauth/google/callback?error=access_denied")
    assert response.headers["location"] == "/login?error=oauth_denied"


def _start(client, provider):
    response = client.get(f"/api/v1/auth/oauth/{provider}/login")
    return parse_qs(urlparse(response.headers["location"]).query)["state"][0]


@respx.mock
def test_google_first_login_registers_user_and_returns_token(db_client, db_session, configured):
    respx.post(oauth.PROVIDERS["google"].token_url).mock(
        return_value=httpx.Response(200, json={"access_token": "tok"})
    )
    respx.get(oauth.GOOGLE_USERINFO_URL).mock(
        return_value=httpx.Response(
            200, json={"sub": "123", "email": "ana@example.com", "email_verified": True}
        )
    )
    state = _start(db_client, "google")
    response = db_client.get(f"/api/v1/auth/oauth/google/callback?code=abc&state={state}")

    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith("/auth/callback#access_token=")

    token = parse_qs(location.split("#", 1)[1])["access_token"][0]
    me = db_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "ana"
    assert me.json()["auth_provider"] == "google"
    assert db_session.query(User).filter_by(provider_user_id="123").one().password_hash is None


@respx.mock
def test_github_login_reuses_existing_account_and_uses_verified_email(
    db_client, db_session, configured
):
    respx.post(oauth.PROVIDERS["github"].token_url).mock(
        return_value=httpx.Response(200, json={"access_token": "tok"})
    )
    respx.get(oauth.GITHUB_USER_URL).mock(
        return_value=httpx.Response(200, json={"id": 77, "login": "Octo"})
    )
    respx.get(oauth.GITHUB_EMAILS_URL).mock(
        return_value=httpx.Response(
            200,
            json=[
                {"email": "sin@example.com", "verified": False, "primary": True},
                {"email": "octo@example.com", "verified": True, "primary": False},
            ],
        )
    )
    for _ in range(2):
        state = _start(db_client, "github")
        response = db_client.get(f"/api/v1/auth/oauth/github/callback?code=abc&state={state}")
        assert response.headers["location"].startswith("/auth/callback#access_token=")

    users = db_session.query(User).filter_by(provider_user_id="77").all()
    assert len(users) == 1
    assert users[0].username == "octo"
    assert users[0].email == "octo@example.com"


@respx.mock
def test_provider_failure_goes_back_to_login(db_client, configured):
    respx.post(oauth.PROVIDERS["google"].token_url).mock(return_value=httpx.Response(400))
    state = _start(db_client, "google")
    response = db_client.get(f"/api/v1/auth/oauth/google/callback?code=abc&state={state}")
    assert response.headers["location"] == "/login?error=oauth_failed"


@respx.mock
def test_disabled_account_cannot_login(db_client, db_session, configured):
    db_session.add(
        User(
            username="baneado",
            password_hash=None,
            auth_provider="google",
            provider_user_id="9",
            is_active=False,
        )
    )
    db_session.commit()
    respx.post(oauth.PROVIDERS["google"].token_url).mock(
        return_value=httpx.Response(200, json={"access_token": "tok"})
    )
    respx.get(oauth.GOOGLE_USERINFO_URL).mock(
        return_value=httpx.Response(200, json={"sub": "9", "email": "b@example.com"})
    )
    state = _start(db_client, "google")
    response = db_client.get(f"/api/v1/auth/oauth/google/callback?code=abc&state={state}")
    assert response.headers["location"] == "/login?error=account_disabled"


def test_social_account_cannot_use_password_login(db_client, db_session):
    db_session.add(
        User(username="social", password_hash=None, auth_provider="github", provider_user_id="5")
    )
    db_session.commit()
    response = db_client.post(
        "/api/v1/auth/login", json={"username": "social", "password": "cualquiera-larga-123"}
    )
    assert response.status_code == 401
