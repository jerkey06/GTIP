"""Dependencias compartidas por los routers de la API."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import InvalidTokenError, decode_access_token, decode_clerk_token
from app.db.session import get_db
from app.models import User
from app.repositories import users as users_repo
from app.services import clerk as clerk_service

DbSession = Annotated[Session, Depends(get_db)]

_bearer = HTTPBearer(auto_error=False, description="Token devuelto por POST /api/v1/auth/login")


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado o token inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    """Exige un token válido y una cuenta activa. Úsala en cada endpoint protegido."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    token = credentials.credentials
    user: User | None
    try:
        user = users_repo.get_by_id(db, int(decode_access_token(token)))
    except (InvalidTokenError, ValueError):
        # No es un token de la API: puede ser una sesión de Clerk.
        if get_settings().clerk_issuer_url is None:
            raise _unauthorized() from None
        try:
            user = clerk_service.get_or_create_user(db, decode_clerk_token(token))
        except InvalidTokenError:
            raise _unauthorized() from None

    if user is None or not user.is_active:
        raise _unauthorized()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
