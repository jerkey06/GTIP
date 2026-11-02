"""Detección y normalización de indicadores de compromiso (ADD §9.1).

Las reglas son específicas por tipo y no cambian el significado del indicador:
solo eliminan diferencias de escritura (mayúsculas en el host, ceros en IPv6,
puerto por defecto…). La ruta y la consulta de una URL se conservan tal cual.
"""

import ipaddress
import re
from urllib.parse import urlsplit, urlunsplit

from app.domain.enums import IndicatorType

_HEX = re.compile(r"^[0-9a-fA-F]+$")
_HASH_LENGTHS = {32: IndicatorType.MD5, 40: IndicatorType.SHA1, 64: IndicatorType.SHA256}
_DOMAIN_LABEL = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")
_DEFAULT_PORTS = {"http": 80, "https": 443, "ftp": 21}


class InvalidIndicatorError(ValueError):
    """El valor no es un indicador válido del tipo indicado."""


def detect_type(value: str) -> IndicatorType | None:
    """Clasifica un valor escrito por el usuario. ``None`` si no encaja en ningún tipo."""
    value = value.strip()
    if not value:
        return None
    if _HEX.match(value) and len(value) in _HASH_LENGTHS:
        return _HASH_LENGTHS[len(value)]
    try:
        address = ipaddress.ip_address(value.strip("[]"))
    except ValueError:
        pass
    else:
        return IndicatorType.IPV4 if address.version == 4 else IndicatorType.IPV6
    if "://" in value:
        return IndicatorType.URL
    try:
        normalize_domain(value)
    except InvalidIndicatorError:
        return None
    return IndicatorType.DOMAIN


def normalize(indicator_type: IndicatorType, value: str) -> str:
    """Devuelve el valor normalizado o lanza ``InvalidIndicatorError``."""
    value = value.strip()
    if not value:
        raise InvalidIndicatorError("El valor está vacío")
    match indicator_type:
        case IndicatorType.IPV4 | IndicatorType.IPV6:
            return _normalize_ip(indicator_type, value)
        case IndicatorType.DOMAIN:
            return normalize_domain(value)
        case IndicatorType.URL:
            return normalize_url(value)
        case IndicatorType.MD5 | IndicatorType.SHA1 | IndicatorType.SHA256:
            return _normalize_hash(indicator_type, value)
    raise InvalidIndicatorError(f"Tipo de indicador no admitido: {indicator_type}")


def _normalize_ip(indicator_type: IndicatorType, value: str) -> str:
    try:
        address = ipaddress.ip_address(value.strip("[]"))
    except ValueError:
        raise InvalidIndicatorError(f"{value!r} no es una dirección IP válida") from None
    expected = 4 if indicator_type is IndicatorType.IPV4 else 6
    if address.version != expected:
        raise InvalidIndicatorError(f"{value!r} no es una dirección IPv{expected}")
    return address.compressed


def normalize_domain(value: str) -> str:
    domain = value.strip().rstrip(".").lower()
    try:
        domain = domain.encode("idna").decode("ascii")
    except UnicodeError:
        raise InvalidIndicatorError(f"{value!r} no es un dominio válido") from None
    labels = domain.split(".")
    if len(domain) > 253 or len(labels) < 2 or not all(_DOMAIN_LABEL.match(x) for x in labels):
        raise InvalidIndicatorError(f"{value!r} no es un dominio válido")
    if labels[-1].isdigit():
        raise InvalidIndicatorError(f"{value!r} no es un dominio válido")
    return domain


def normalize_url(value: str) -> str:
    try:
        parts = urlsplit(value.strip())
        port = parts.port
    except ValueError:
        raise InvalidIndicatorError(f"{value!r} no es una URL válida") from None
    scheme = parts.scheme.lower()
    host = parts.hostname
    if not scheme or not host:
        raise InvalidIndicatorError(f"{value!r} no es una URL válida")
    if ":" in host:  # IPv6 literal
        host = f"[{ipaddress.ip_address(host).compressed}]"
    else:
        try:
            host = host.encode("idna").decode("ascii")
        except UnicodeError:
            pass  # se conserva tal cual: no inventamos un host distinto
    netloc = host if port in (None, _DEFAULT_PORTS.get(scheme)) else f"{host}:{port}"
    if parts.username:
        userinfo = parts.username + (f":{parts.password}" if parts.password else "")
        netloc = f"{userinfo}@{netloc}"
    # Sin fragmento: nunca llega al servidor, así que no distingue dos URLs.
    return urlunsplit((scheme, netloc, parts.path or "/", parts.query, ""))


def _normalize_hash(indicator_type: IndicatorType, value: str) -> str:
    if not _HEX.match(value) or _HASH_LENGTHS.get(len(value)) is not indicator_type:
        raise InvalidIndicatorError(f"{value!r} no es un hash {indicator_type.name} válido")
    return value.lower()
