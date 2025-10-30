from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app


def test_extract_user_json(monkeypatch) -> None:
    client = TestClient(app)

    async def fake_extract_user(text: str, stream: bool = False):
        from app.schemas import ExtractedUser

        return ExtractedUser(name="Jane", email="jane@example.com")

    with patch(
        "app.ai_service.AIService.extract_user", new=AsyncMock(side_effect=fake_extract_user)
    ):
        res = client.post("/extract-user", json={"text": "Jane <jane@example.com>"})
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "Jane"
        assert data["email"] == "jane@example.com"


def test_extract_user_stream(monkeypatch) -> None:
    client = TestClient(app)

    async def fake_stream(text: str, stream: bool = True):  # type: ignore[override]
        async def gen():
            yield "Jane"
            yield " <jane@example.com>"

        return gen()

    with patch("app.ai_service.AIService.extract_user", new=AsyncMock(side_effect=fake_stream)):
        res = client.post("/extract-user?stream=true", json={"text": "Jane <jane@example.com>"})
        assert res.status_code == 200
        body = res.text
        assert "Jane" in body
