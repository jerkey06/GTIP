"""Hash de contraseñas (Argon2id) y tokens de acceso JWT (ADD §12.2)."""

from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from jwt import PyJWKClient

from app.core.config import get_settings

MIN_PASSWORD_LENGTH = 12

# Parámetros por defecto de argon2-cffi: Argon2id con los valores recomendados (RFC 9106).
_hasher = PasswordHasher()
# Hash fijo para gastar el mismo tiempo cuando el usuario no existe y no revelar
# qué nombres de usuario son válidos midiendo el tiempo de respuesta.
_DUMMY_HASH = _hasher.hash("gtip-dummy-password")


class InvalidTokenError(Exception):
    """El token falta, está mal formado, tiene una firma inválida o expiró."""


def validate_password_strength(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres.")


def hash_password(password: str) -> str:
    validate_password_strength(password)
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Compara en tiempo constante. Con ``password_hash=None`` verifica un hash ficticio."""
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    expires = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {"sub": str(subject), "iat": now, "exp": expires, "type": "access"}
    return jwt.encode(payload, settings.app_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """Valida firma, expiración y campos obligatorios. Devuelve el ``sub`` (id de usuario)."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.app_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "iat", "exp"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc
    if payload.get("type") != "access":
        raise InvalidTokenError("Tipo de token inválido")
    return payload["sub"]


_jwks_clients: dict[str, PyJWKClient] = {}


def _jwks_client(issuer: str) -> PyJWKClient:
    """Cliente JWKS por emisor; PyJWKClient guarda en caché las claves públicas de Clerk."""
    if issuer not in _jwks_clients:
        _jwks_clients[issuer] = PyJWKClient(f"{issuer}/.well-known/jwks.json", lifespan=3600)
    return _jwks_clients[issuer]


def decode_clerk_token(token: str) -> dict:
    """Valida un token de sesión de Clerk (RS256, emisor, expiración y origen autorizado).

    Devuelve las claims; ``sub`` es el id estable del usuario en Clerk.
    """
    settings = get_settings()
    issuer = settings.clerk_issuer_url
    if issuer is None:
        raise InvalidTokenError("Clerk no está configurado")
    try:
        signing_key = _jwks_client(issuer).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer,
            options={"require": ["sub", "exp", "iat"], "verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    # ``azp`` es el origen que pidió el token; evita aceptar tokens emitidos para otro sitio.
    allowed = {settings.public_url.rstrip("/"), "http://localhost:5173"}
    azp = claims.get("azp")
    if azp is not None and azp.rstrip("/") not in allowed:
        raise InvalidTokenError("Origen no autorizado (azp)")
    return claims
