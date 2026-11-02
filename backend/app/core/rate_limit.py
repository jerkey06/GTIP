"""Límite sencillo de intentos por cliente, en memoria del proceso.

Basta para frenar ataques de fuerza bruta contra el login en el MVP (un único proceso
de API). Con varias réplicas habría que moverlo a PostgreSQL o al proxy inverso.
"""

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, window_seconds: float = 60.0) -> None:
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int) -> bool:
        """Registra un intento y dice si está dentro del límite de la ventana."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


login_limiter = RateLimiter()
