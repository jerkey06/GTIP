import hmac
import logging
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.api.dependencies import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.rate_limit import login_limiter
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, TokenResponse, UserRead
from app.services import oauth
from app.services.auth import authenticate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

STATE_COOKIE = "gtip_oauth_state"
STATE_COOKIE_PATH = "/api/v1/auth/oauth"


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"description": "Credenciales inválidas"},
        429: {"description": "Demasiados intentos"},
    },
)
def login(body: LoginRequest, db: DbSession, request: Request) -> TokenResponse:
    settings = get_settings()
    client = request.client.host if request.client else "desconocido"
    if not login_limiter.allow(client, settings.login_rate_limit_per_minute):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Espera un momento.",
            headers={"Retry-After": "60"},
        )
    user = authenticate(db, body.username, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    minutes = settings.access_token_expire_minutes
    return TokenResponse(access_token=create_access_token(user.id), expires_in=minutes * 60)


@router.get("/me", response_model=UserRead, responses={401: {"description": "No autenticado"}})
def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.get("/providers", responses={200: {"description": "Proveedores de login social activos"}})
def providers() -> dict[str, bool]:
    """Qué botones de inicio de sesión social debe mostrar el frontend."""
    return oauth.enabled_providers(get_settings())


def _to_login(error: str) -> RedirectResponse:
    response = RedirectResponse(f"/login?{urlencode({'error': error})}", status_code=302)
    response.delete_cookie(STATE_COOKIE, path=STATE_COOKIE_PATH)
    return response


def _known_provider(provider: str) -> str:
    if provider not in oauth.PROVIDERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proveedor desconocido")
    return provider


@router.get(
    "/oauth/{provider}/login",
    status_code=status.HTTP_302_FOUND,
    responses={302: {"description": "Redirige al proveedor"}, 404: {"description": "Desconocido"}},
)
def oauth_login(provider: str) -> RedirectResponse:
    """Inicia el flujo: guarda un ``state`` aleatorio en una cookie y redirige al proveedor."""
    settings = get_settings()
    provider = _known_provider(provider)
    if oauth.credentials(settings, provider) is None:
        return _to_login("oauth_not_configured")

    state = oauth.new_state()
    response = RedirectResponse(oauth.authorize_url(settings, provider, state), status_code=302)
    response.set_cookie(
        STATE_COOKIE,
        state,
        max_age=600,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path=STATE_COOKIE_PATH,
    )
    return response


@router.get(
    "/oauth/{provider}/callback",
    status_code=status.HTTP_302_FOUND,
    responses={302: {"description": "Vuelve al frontend con el token o con un error"}},
)
def oauth_callback(
    provider: str,
    request: Request,
    db: DbSession,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    """Cierra el flujo: valida ``state``, crea o busca la cuenta y entrega el JWT de la API.

    El token viaja en el fragmento de la URL (``#access_token=…``) para que no llegue
    a registros de servidores ni al encabezado Referer.
    """
    settings = get_settings()
    provider = _known_provider(provider)
    if error:
        return _to_login("oauth_denied")

    cookie_state = request.cookies.get(STATE_COOKIE)
    if not code or not state or not cookie_state or not hmac.compare_digest(state, cookie_state):
        return _to_login("oauth_state")

    try:
        profile = oauth.fetch_profile(settings, provider, code)
    except oauth.OAuthError:
        logger.warning("Fallo en el login con %s", provider, exc_info=True)
        return _to_login("oauth_failed")

    user = oauth.get_or_create_user(db, profile)
    if user is None:
        return _to_login("account_disabled")

    token = create_access_token(user.id)
    response = RedirectResponse(
        f"/auth/callback#{urlencode({'access_token': token})}", status_code=302
    )
    response.delete_cookie(STATE_COOKIE, path=STATE_COOKIE_PATH)
    return response
