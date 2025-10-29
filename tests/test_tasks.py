from __future__ import annotations

# ruff: noqa: S101 - pytest-style asserts for clarity
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app


def test_enqueue_echo_task_returns_task_id() -> None:
    client = TestClient(app)
    fake_result = MagicMock(id="task-123")

    with patch("app.routers_tasks.echo_task.delay", return_value=fake_result):
        res = client.post("/tasks/echo", json={"text": "hello"})

    assert res.status_code == 202
    assert res.json()["task_id"] == "task-123"


def test_fetch_task_includes_status_and_result() -> None:
    client = TestClient(app)
    fake_async = MagicMock()
    fake_async.status = "SUCCESS"
    fake_async.result = "PROCESSED"
    fake_async.successful.return_value = True
    fake_async.failed.return_value = False
    fake_async.info = {"processed_docs": 2}

    with patch("app.routers_tasks.AsyncResult", return_value=fake_async):
        res = client.get("/tasks/task-123")

    assert res.status_code == 200
    payload = res.json()
    assert payload["task_id"] == "task-123"
    assert payload["status"] == "SUCCESS"
    assert payload["result"] == "PROCESSED"
    assert payload["meta"] == {"processed_docs": 2}
