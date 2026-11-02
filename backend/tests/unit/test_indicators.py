import pytest

from app.domain.enums import IndicatorType
from app.domain.indicators import InvalidIndicatorError, detect_type, normalize
from app.domain.records import IndicatorRecord

MD5 = "D41D8CD98F00B204E9800998ECF8427E"
SHA1 = "da39a3ee5e6b4b0d3255bfef95601890afd80709"
SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("8.8.8.8", IndicatorType.IPV4),
        ("2001:0db8::0001", IndicatorType.IPV6),
        ("Example.COM", IndicatorType.DOMAIN),
        ("http://evil.example/payload.exe", IndicatorType.URL),
        (MD5, IndicatorType.MD5),
        (SHA1, IndicatorType.SHA1),
        (SHA256, IndicatorType.SHA256),
        ("no es nada", None),
        ("", None),
    ],
)
def test_detect_type(value, expected):
    assert detect_type(value) is expected


@pytest.mark.parametrize(
    ("indicator_type", "value", "expected"),
    [
        (IndicatorType.IPV4, " 10.0.0.1 ", "10.0.0.1"),
        (IndicatorType.IPV6, "2001:0DB8:0000::0001", "2001:db8::1"),
        (IndicatorType.DOMAIN, "WWW.Example.com.", "www.example.com"),
        (IndicatorType.DOMAIN, "bücher.de", "xn--bcher-kva.de"),
        (IndicatorType.MD5, MD5, MD5.lower()),
        (
            IndicatorType.URL,
            "HTTP://Evil.Example:80/Path/File.EXE?a=B#frag",
            "http://evil.example/Path/File.EXE?a=B",
        ),
        (IndicatorType.URL, "https://evil.example:8443", "https://evil.example:8443/"),
        (IndicatorType.URL, "http://[2001:DB8::1]/x", "http://[2001:db8::1]/x"),
    ],
)
def test_normalize(indicator_type, value, expected):
    assert normalize(indicator_type, value) == expected


@pytest.mark.parametrize(
    ("indicator_type", "value"),
    [
        (IndicatorType.IPV4, "2001:db8::1"),
        (IndicatorType.IPV4, "999.1.1.1"),
        (IndicatorType.DOMAIN, "localhost"),
        (IndicatorType.DOMAIN, "-malo-.com"),
        (IndicatorType.URL, "evil.example/sin-esquema"),
        (IndicatorType.SHA256, MD5),
        (IndicatorType.MD5, "z" * 32),
    ],
)
def test_invalid_values_are_rejected(indicator_type, value):
    with pytest.raises(InvalidIndicatorError):
        normalize(indicator_type, value)


def test_indicator_record_from_value_keeps_original():
    record = IndicatorRecord.from_value(IndicatorType.DOMAIN, " Evil.Example ")
    assert record.value == "Evil.Example"
    assert record.normalized_value == "evil.example"
