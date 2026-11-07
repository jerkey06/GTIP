from fastapi.testclient import TestClient

from app import main
from app.core.config import get_settings


def test_embedded_worker_is_off_by_default(monkeypatch):
    monkeypatch.delenv("EMBEDDED_WORKER", raising=False)
    get_settings.cache_clear()
    started = []
    monkeypatch.setattr("app.ingestion.worker.run_forever", lambda stop: started.append(stop))
    try:
        with TestClient(main.create_app()):
            pass
    finally:
        get_settings.cache_clear()
    assert started == []


def test_embedded_worker_runs_in_a_thread_and_stops_with_the_app(monkeypatch):
    import threading

    monkeypatch.setenv("EMBEDDED_WORKER", "true")
    get_settings.cache_clear()
    seen = {}

    def fake_run_forever(stop):
        seen["thread"] = threading.current_thread().name
        stop.wait(5)
        seen["stopped"] = stop.is_set()

    monkeypatch.setattr("app.ingestion.worker.run_forever", fake_run_forever)
    try:
        with TestClient(main.create_app()):
            pass
        for thread in threading.enumerate():
            if thread.name == "gtip-worker":
                thread.join(timeout=5)
    finally:
        get_settings.cache_clear()
    assert seen["thread"] == "gtip-worker"
    assert seen["stopped"] is True
