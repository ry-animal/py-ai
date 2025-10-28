from __future__ import annotations

# ruff: noqa: S101 - pytest-style asserts are expected in tests
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app


def test_agent_chat_json() -> None:
    client = TestClient(app)

    async def fake_answer(question: str, stream: bool = False):
        return "hello"

    with patch("app.agent_service.AgentService.answer", new=AsyncMock(side_effect=fake_answer)):
        res = client.get("/agent/chat", params={"q": "hi"})
        assert res.status_code == 200
        assert res.json()["answer"] == "hello"


def test_agent_chat_stream() -> None:
    client = TestClient(app)

    async def fake_answer(question: str, stream: bool = True):  # type: ignore[override]
        async def gen():
            yield "part1"
            yield "part2"

        return gen()

    with patch("app.agent_service.AgentService.answer", new=AsyncMock(side_effect=fake_answer)):
        res = client.get("/agent/chat", params={"q": "hi", "stream": "true"})
        assert res.status_code == 200
        assert "part1" in res.text
