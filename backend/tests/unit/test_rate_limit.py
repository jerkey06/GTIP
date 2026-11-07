from app.core import rate_limit
from app.core.rate_limit import RateLimiter


def test_limit_per_key():
    limiter = RateLimiter(window_seconds=60)
    assert all(limiter.allow("1.2.3.4", 3) for _ in range(3))
    assert not limiter.allow("1.2.3.4", 3)
    assert limiter.allow("5.6.7.8", 3)


def test_window_expires(monkeypatch):
    clock = iter([0.0, 30.0, 61.0])
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: next(clock))
    limiter = RateLimiter(window_seconds=60)
    assert limiter.allow("ip", 1)
    assert not limiter.allow("ip", 1)
    assert limiter.allow("ip", 1)
