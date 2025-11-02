from __future__ import annotations

import os
import pytest
from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from app.middleware_guardrails import refresh_rate_limiter


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment with required API keys and mock AI services."""
    # Mock OpenAI API calls
    mock_completion = {
        "id": "test-completion",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4o",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Test response from AI agent",
                    "tool_calls": [
                        {
                            "id": "test-tool-call",
                            "type": "function",
                            "function": {
                                "name": "route_query",
                                "arguments": (
                                    '{"route": "rag", "reason": "Test routing", '
                                    '"confidence": 0.8}'
                                ),
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }

    with (
        patch.dict(
            os.environ,
            {
                "ANTHROPIC_API_KEY": "test-anthropic-key",
                "OPENAI_API_KEY": "test-openai-key",
            },
        ),
        patch(
            "openai.resources.chat.completions.AsyncCompletions.create", new_callable=AsyncMock
        ) as mock_openai,
        patch(
            "anthropic.resources.messages.AsyncMessages.create", new_callable=AsyncMock
        ) as mock_anthropic,
    ):
        mock_openai.return_value = mock_completion
        mock_anthropic.return_value = AsyncMock(
            content=[AsyncMock(text="Test response from Anthropic")]
        )

        yield

    get_settings.cache_clear()  # type: ignore[attr-defined]
    refresh_rate_limiter()


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    app = create_app()
    return TestClient(app)
