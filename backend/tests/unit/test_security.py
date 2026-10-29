from datetime import timedelta

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

PASSWORD = "correct horse battery"


def test_hash_is_argon2id_and_not_plaintext():
    hashed = hash_password(PASSWORD)
    assert hashed.startswith("$argon2id$")
    assert PASSWORD not in hashed


def test_verify_password():
    hashed = hash_password(PASSWORD)
    assert verify_password(PASSWORD, hashed)
    assert not verify_password("otra contraseña larga", hashed)


def test_verify_password_without_user_is_false():
    assert not verify_password(PASSWORD, None)


def test_verify_password_with_corrupt_hash_is_false():
    assert not verify_password(PASSWORD, "no-es-un-hash")


def test_short_password_is_rejected():
    with pytest.raises(ValueError):
        hash_password("corta")


def test_token_roundtrip():
    token = create_access_token(42)
    assert decode_access_token(token) == "42"


def test_expired_token_is_rejected():
    token = create_access_token(42, expires_delta=timedelta(seconds=-1))
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_token_signed_with_other_key_is_rejected():
    settings = get_settings()
    forged = jwt.encode(
        {"sub": "42", "iat": 0, "exp": 9999999999, "type": "access"},
        "otra-clave-distinta-de-la-configurada",
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(forged)


def test_unsigned_token_is_rejected():
    forged = jwt.encode({"sub": "42", "iat": 0, "exp": 9999999999, "type": "access"}, None, "none")
    with pytest.raises(InvalidTokenError):
        decode_access_token(forged)


def test_token_without_exp_is_rejected():
    settings = get_settings()
    token = jwt.encode(
        {"sub": "42", "iat": 0, "type": "access"},
        settings.app_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)
