from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.repositories.users import create_user

PASSWORD = "contraseña-de-prueba-larga"


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def user(db_session):
    user = create_user(db_session, "Analista", PASSWORD)
    db_session.commit()
    return user


def _login(client, username, password):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


def test_login_returns_token_and_me_works(client, user):
    response = _login(client, "analista", PASSWORD)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["username"] == "analista"
    assert "password_hash" not in me.json()


def test_username_is_case_insensitive(client, user):
    assert _login(client, "ANALISTA", PASSWORD).status_code == 200


@pytest.mark.parametrize(
    ("username", "password"), [("analista", "incorrecta-larga"), ("nadie", PASSWORD)]
)
def test_invalid_credentials_get_same_401(client, user, username, password):
    response = _login(client, username, password)
    assert response.status_code == 401
    assert response.json()["detail"] == "Usuario o contraseña incorrectos"


def test_inactive_user_cannot_login_nor_use_token(client, db_session, user):
    token = create_access_token(user.id)
    user.is_active = False
    db_session.commit()

    assert _login(client, "analista", PASSWORD).status_code == 401
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 401


def test_me_requires_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("token", ["basura", create_access_token(1, timedelta(seconds=-1))])
def test_me_rejects_bad_or_expired_token(client, token):
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_login_validates_body(client):
    assert client.post("/api/v1/auth/login", json={"username": ""}).status_code == 422
