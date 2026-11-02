import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.repositories.users import create_user


@pytest.fixture
def api_user(db_session):
    user = create_user(db_session, "analista-api", "contraseña-de-prueba-larga")
    db_session.commit()
    return user


@pytest.fixture
def auth_client(db_session, api_user):
    """Cliente con la sesión de pruebas y un token válido en cada petición."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    client.headers["Authorization"] = f"Bearer {create_access_token(api_user.id)}"
    yield client
    app.dependency_overrides.clear()
