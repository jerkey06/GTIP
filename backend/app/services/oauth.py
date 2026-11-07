"""Inicio de sesión con Google y GitHub (OAuth 2.0, flujo de código de autorización).

La API actúa como cliente confidencial: intercambia el código por un token con el
secreto del cliente, lee el perfil y emite el mismo JWT de la API que el login con
contraseña. Los tokens del proveedor se descartan; no se guardan.
"""

import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import User

TIMEOUT = httpx.Timeout(10.0)


class OAuthError(Exception):
    """El proveedor rechazó el intercambio o no entregó un perfil utilizable."""


@dataclass(frozen=True)
class Provider:
    key: str
    authorize_url: str
    token_url: str
    scope: str


PROVIDERS: dict[str, Provider] = {
    "google": Provider(
        key="google",
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        scope="openid email profile",
    ),
    "github": Provider(
        key="github",
        authorize_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        scope="read:user user:email",
    ),
}

GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


@dataclass(frozen=True)
class Profile:
    provider: str
    provider_user_id: str
    email: str | None
    suggested_username: str


def credentials(settings: Settings, provider: str) -> tuple[str, str] | None:
    """(client_id, client_secret) del proveedor, o None si no está configurado."""
    client_id = getattr(settings, f"{provider}_client_id", None)
    client_secret = getattr(settings, f"{provider}_client_secret", None)
    if client_id and client_secret:
        return client_id, client_secret
    return None


def enabled_providers(settings: Settings) -> dict[str, bool]:
    return {key: credentials(settings, key) is not None for key in PROVIDERS}


def redirect_uri(settings: Settings, provider: str) -> str:
    return f"{settings.public_url.rstrip('/')}/api/v1/auth/oauth/{provider}/callback"


def new_state() -> str:
    return secrets.token_urlsafe(32)


def authorize_url(settings: Settings, provider: str, state: str) -> str:
    creds = credentials(settings, provider)
    if creds is None:
        raise OAuthError(f"El proveedor {provider} no está configurado")
    spec = PROVIDERS[provider]
    params = {
        "client_id": creds[0],
        "redirect_uri": redirect_uri(settings, provider),
        "response_type": "code",
        "scope": spec.scope,
        "state": state,
    }
    if provider == "google":
        params["prompt"] = "select_account"
    return f"{spec.authorize_url}?{urlencode(params)}"


def fetch_profile(settings: Settings, provider: str, code: str) -> Profile:
    """Cambia el código por un token de acceso y devuelve el perfil verificado."""
    creds = credentials(settings, provider)
    if creds is None:
        raise OAuthError(f"El proveedor {provider} no está configurado")
    spec = PROVIDERS[provider]
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            token_response = client.post(
                spec.token_url,
                data={
                    "client_id": creds[0],
                    "client_secret": creds[1],
                    "code": code,
                    "redirect_uri": redirect_uri(settings, provider),
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )
            token_response.raise_for_status()
            access_token = token_response.json().get("access_token")
            if not access_token:
                raise OAuthError("El proveedor no devolvió un token de acceso")
            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
            if provider == "google":
                return _google_profile(client, headers)
            return _github_profile(client, headers)
    except (httpx.HTTPError, ValueError) as exc:
        raise OAuthError(f"Fallo al hablar con {provider}: {exc}") from exc


def _google_profile(client: httpx.Client, headers: dict[str, str]) -> Profile:
    response = client.get(GOOGLE_USERINFO_URL, headers=headers)
    response.raise_for_status()
    data = response.json()
    email = data.get("email") if data.get("email_verified") else None
    subject = data.get("sub")
    if not subject:
        raise OAuthError("Google no devolvió un identificador de usuario")
    base = email.split("@")[0] if email else str(data.get("name") or "usuario")
    return Profile("google", str(subject), email, base)


def _github_profile(client: httpx.Client, headers: dict[str, str]) -> Profile:
    response = client.get(GITHUB_USER_URL, headers=headers)
    response.raise_for_status()
    data = response.json()
    if data.get("id") is None:
        raise OAuthError("GitHub no devolvió un identificador de usuario")

    email: str | None = None
    emails = client.get(GITHUB_EMAILS_URL, headers=headers)
    if emails.status_code == 200:
        verified = [e for e in emails.json() if e.get("verified") and e.get("email")]
        primary = next((e for e in verified if e.get("primary")), None)
        chosen = primary or (verified[0] if verified else None)
        email = chosen["email"] if chosen else None
    return Profile("github", str(data["id"]), email, str(data.get("login") or "usuario"))


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9._-]+", "-", value.strip().lower()).strip("-._")
    return slug[:48] or "usuario"


def _unique_username(session: Session, wanted: str) -> str:
    base = _slug(wanted)
    candidate = base
    while session.scalar(select(User.id).where(User.username == candidate)) is not None:
        candidate = f"{base}-{secrets.token_hex(2)}"
    return candidate


def get_or_create_user(session: Session, profile: Profile) -> User | None:
    """Usuario de la identidad del proveedor; lo crea si es la primera vez (registro).

    Devuelve None si la cuenta existe pero está desactivada. No se enlaza con cuentas de
    contraseña por correo: así un correo ajeno no puede reclamar una cuenta existente.
    """
    user = session.scalar(
        select(User).where(
            User.auth_provider == profile.provider,
            User.provider_user_id == profile.provider_user_id,
        )
    )
    if user is None:
        user = User(
            username=_unique_username(session, profile.suggested_username),
            password_hash=None,
            email=profile.email,
            auth_provider=profile.provider,
            provider_user_id=profile.provider_user_id,
        )
        session.add(user)
        session.flush()
    elif profile.email and user.email != profile.email:
        user.email = profile.email

    if not user.is_active:
        return None
    user.last_login_at = datetime.now(UTC)
    session.commit()
    return user
