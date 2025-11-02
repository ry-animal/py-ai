from __future__ import annotations

import functools

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env",), env_prefix="", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"
    cors_allow_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # AI Provider Configuration
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
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

    # Database Configuration
    # MongoDB for document storage
    mongodb_url: str | None = None
    mongodb_database: str = "py_ai_platform"

    # PostgreSQL for metadata and sessions
    postgres_url: str | None = None
    postgres_database: str = "py_ai_metadata"

    # Redis for caching and Celery
    redis_url: str | None = None

    # Vector Database Configuration
    vector_db_type: str = "chroma"  # "vertex", "snowflake", "mongodb_vector", "cockroach", "chroma"

    # Vertex AI Configuration
    gcp_project_id: str | None = None
    gcp_region: str = "us-central1"
    vertex_index_endpoint_id: str | None = None

    # Snowflake Configuration
    snowflake_account: str | None = None
    snowflake_user: str | None = None
    snowflake_password: str | None = None
    snowflake_database: str | None = None
    snowflake_schema: str = "PUBLIC"

    # CockroachDB Configuration (Bonus points! 🎯)
    cockroach_connection_string: str | None = None

    # LightLLM Integration
    lightllm_endpoint: str | None = None
    lightllm_enabled: bool = False

    # Agent Configuration
    agent_memory_max_turns: int = 3
    agent_memory_ttl_seconds: int | None = 86_400

    # Multi-Agent Features
    enable_smart_orchestrator: bool = True
    enable_hybrid_agent: bool = True
    enable_pydantic_agent: bool = True
    enable_langgraph_agent: bool = True

    # Celery / async tasks
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    celery_task_default_queue: str = "default"

    # Security & Performance
    max_request_body_bytes: int = 2_000_000
    rate_limit_requests_per_window: int = 120
    rate_limit_window_seconds: int = 60

    # Monitoring & Observability
    otel_endpoint: str | None = None
    enable_metrics: bool = True
    metrics_port: int = 9090

    # Enterprise Features
    enable_plugins: bool = False
    plugin_directory: str = "plugins"


@functools.lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
