from __future__ import annotations

import functools

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env",), env_prefix="", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"
    cors_allow_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    # AI provider defaults
    model_provider: str = "openai"  # "openai" or "ollama"
    model_name: str = "gpt-4o-mini"
    claude_model: str = "claude-3-5-sonnet-latest"
    streaming_enabled: bool = True
    # Embeddings / RAG
    embedding_model: str = "all-MiniLM-L6-v2"
    # Web search (Tavily)
    tavily_api_key: str | None = None
    max_web_results: int = 3
    tavily_search_depth: str = "basic"  # "basic" or "advanced"
    # Agent memory
    redis_url: str | None = None
    agent_memory_max_turns: int = 3
    agent_memory_ttl_seconds: int | None = 86_400
    # Celery / async tasks
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    celery_task_default_queue: str = "default"
    # Request guardrails
    max_request_body_bytes: int = 2_000_000
    rate_limit_requests_per_window: int = 120
    rate_limit_window_seconds: int = 60


@functools.lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
