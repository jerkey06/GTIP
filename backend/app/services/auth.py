from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.security import password_needs_rehash, verify_password
from app.models import User
from app.repositories import users as users_repo


def authenticate(session: Session, username: str, password: str) -> User | None:
    """Devuelve el usuario si las credenciales son válidas y la cuenta está activa.

    No distingue entre usuario inexistente, contraseña errónea o cuenta desactivada,
    para no revelar qué cuentas existen. Hace commit del último acceso.
    """
    user = users_repo.get_by_username(session, username)
    password_ok = verify_password(password, user.password_hash if user else None)
    if user is None or not password_ok or not user.is_active:
        return None

    if password_needs_rehash(user.password_hash):
        users_repo.set_password(session, user, password)
    user.last_login_at = datetime.now(UTC)
    session.commit()
    return user
