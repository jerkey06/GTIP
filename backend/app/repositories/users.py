from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User


def normalize_username(username: str) -> str:
    return username.strip().lower()


def get_by_id(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)


def get_by_username(session: Session, username: str) -> User | None:
    return session.scalar(select(User).where(User.username == normalize_username(username)))


def create_user(session: Session, username: str, password: str) -> User:
    """Crea una cuenta activa con la contraseña hasheada en Argon2id. No hace commit."""
    user = User(username=normalize_username(username), password_hash=hash_password(password))
    session.add(user)
    session.flush()
    return user


def set_password(session: Session, user: User, password: str) -> None:
    user.password_hash = hash_password(password)
    session.flush()
