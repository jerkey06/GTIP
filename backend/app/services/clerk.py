"""Usuarios que entran con Clerk: se crean la primera vez que presentan un token válido."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User
from app.services.oauth import unique_username

PROVIDER = "clerk"


def _suggested_username(claims: dict, subject: str) -> str:
    for key in ("username", "email", "name"):
        value = claims.get(key)
        if isinstance(value, str) and value.strip():
            return value.split("@")[0]
    return f"clerk-{subject[-8:]}"


def _find(session: Session, subject: str) -> User | None:
    return session.scalar(
        select(User).where(User.auth_provider == PROVIDER, User.provider_user_id == subject)
    )


def get_or_create_user(session: Session, claims: dict) -> User:
    """Usuario del ``sub`` de Clerk. Crea la cuenta si es la primera vez (registro abierto)."""
    subject = str(claims["sub"])
    user = _find(session, subject)
    if user is not None:
        return user

    email = claims.get("email") if isinstance(claims.get("email"), str) else None
    user = User(
        username=unique_username(session, _suggested_username(claims, subject)),
        password_hash=None,
        email=email,
        auth_provider=PROVIDER,
        provider_user_id=subject,
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        # Dos primeras peticiones simultáneas: la otra ya creó la cuenta.
        session.rollback()
        existing = _find(session, subject)
        if existing is None:
            raise
        return existing
    return user
