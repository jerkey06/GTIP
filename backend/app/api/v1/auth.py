from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, TokenResponse, UserRead
from app.services.auth import authenticate

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={401: {"description": "Credenciales inválidas"}},
)
def login(body: LoginRequest, db: DbSession) -> TokenResponse:
    user = authenticate(db, body.username, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    minutes = get_settings().access_token_expire_minutes
    return TokenResponse(access_token=create_access_token(user.id), expires_in=minutes * 60)


@router.get("/me", response_model=UserRead, responses={401: {"description": "No autenticado"}})
def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
