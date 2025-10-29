from __future__ import annotations

import pytest

from app.config import get_settings
from app.middleware_guardrails import refresh_rate_limiter


@pytest.fixture(autouse=True)
def reset_guardrails():
    yield
    get_settings.cache_clear()  # type: ignore[attr-defined]
    refresh_rate_limiter()
