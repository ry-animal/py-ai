from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app


def test_rag_reload_and_ask() -> None:
    client = TestClient(app)
    with patch("app.rag_service.RAGService.ingest", return_value=2) as _ingest:
        res = client.post("/rag/reload", json=[["1", "hello world"], ["2", "another doc"]])
        assert res.status_code == 200
        assert res.json()["ingested"] == 2

    with patch("app.rag_service.RAGService.retrieve", return_value=["hello world"]) as _ret:
        with patch("app.ai_service.AIService.generate_answer", new=AsyncMock(return_value="hi")):
            res = client.get("/ask", params={"q": "hello?"})
            assert res.status_code == 200
            data = res.json()
            assert data["answer"] == "hi"
            assert "hello world" in data["contexts"][0]


def test_rag_ask_streams() -> None:
    client = TestClient(app)
    with patch("app.rag_service.RAGService.retrieve", return_value=["ctx"]) as _ret:
        async def fake_stream(*args, **kwargs):  # type: ignore[no-untyped-def]
            async def gen():
                yield "part1"
                yield "part2"
            return gen()

        with patch("app.ai_service.AIService.generate_answer", new=AsyncMock(side_effect=fake_stream)):
            res = client.get("/ask", params={"q": "hello?", "stream": "true"})
            assert res.status_code == 200
            assert "part1" in res.text


