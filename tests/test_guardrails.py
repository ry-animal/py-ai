from __future__ import annotations

# ruff: noqa: S101 - pytest-style asserts expected
from fastapi.testclient import TestClient

from app import middleware_guardrails as guardrails
from app.config import get_settings
from app.main import create_app
from app.middleware_guardrails import refresh_rate_limiter


def make_client(monkeypatch, **env: str) -> TestClient:
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()  # type: ignore[attr-defined]
    refresh_rate_limiter()
    return TestClient(create_app())


def test_request_size_limit_returns_413(monkeypatch) -> None:
    client = make_client(monkeypatch, MAX_REQUEST_BODY_BYTES="10")
    assert guardrails.get_settings().max_request_body_bytes == 10
    payload = [["doc", "this is definitely larger than ten bytes"]]
    res = client.post("/rag/reload", json=payload, params={"background": "false"})
    assert res.status_code == 413
    assert res.json()["detail"] == "Request body too large."


def test_rate_limiter_blocks_after_threshold(monkeypatch) -> None:
    client = make_client(
        monkeypatch,
        RATE_LIMIT_REQUESTS_PER_WINDOW="2",
        RATE_LIMIT_WINDOW_SECONDS="60",
    )
    assert client.get("/health").status_code == 200
    assert client.get("/health").status_code == 200
    third = client.get("/health")
    assert third.status_code == 429
    data = third.json()
    assert data["detail"] == "Too many requests"
    assert "retry_after" in data
