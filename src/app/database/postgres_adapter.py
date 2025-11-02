"""PostgreSQL adapter for metadata and session management."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

import asyncpg
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)


class AgentSession(BaseModel):
    """Agent session model."""

    session_id: str
    user_id: str | None = None
    agent_type: str  # langgraph, pydantic_ai, hybrid, smart
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = {}
    message_count: int = 0
    total_tokens: int = 0
    avg_response_time: float = 0.0
    status: str = "active"  # active, inactive, expired


class AgentMetrics(BaseModel):
    """Agent performance metrics."""

    metric_id: str
    session_id: str
    agent_type: str
    endpoint: str
    request_timestamp: datetime
    response_time_ms: float
    token_count: int
    success: bool
    error_message: str | None = None
    model_used: str | None = None
    cost_estimate: float = 0.0
    user_feedback: int | None = None  # 1-5 rating


class DocumentProcessingLog(BaseModel):
    """Document processing audit log."""

    log_id: str
    document_id: str
    session_id: str | None = None
    processing_stage: str  # upload, chunking, embedding, indexing, completed
    status: str  # started, in_progress, completed, failed
    timestamp: datetime
    processing_time_ms: float | None = None
    error_details: dict | None = None
    metadata: dict[str, Any] = {}


class PostgreSQLAdapter:
    """PostgreSQL adapter for metadata and session management."""

    def __init__(self, connection_string: str = None):
        settings = get_settings()
        self.connection_string = connection_string or settings.postgres_url
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Establish connection pool to PostgreSQL."""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string, min_size=5, max_size=20, command_timeout=60
            )
            logger.info("Successfully connected to PostgreSQL")

            # Create tables if they don't exist
            await self._create_tables()

        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def disconnect(self) -> None:
        """Close PostgreSQL connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from PostgreSQL")

    async def _create_tables(self) -> None:
        """Create necessary tables and indexes."""
        async with self.pool.acquire() as conn:
            # Agent sessions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_sessions (
                    session_id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255),
                    agent_type VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    metadata JSONB DEFAULT '{}',
                    message_count INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    avg_response_time FLOAT DEFAULT 0.0,
                    status VARCHAR(20) DEFAULT 'active'
                )
            """)

            # Agent metrics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_metrics (
                    metric_id VARCHAR(255) PRIMARY KEY,
                    session_id VARCHAR(255) REFERENCES agent_sessions(session_id),
                    agent_type VARCHAR(50) NOT NULL,
                    endpoint VARCHAR(255) NOT NULL,
                    request_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    response_time_ms FLOAT NOT NULL,
                    token_count INTEGER DEFAULT 0,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    model_used VARCHAR(100),
                    cost_estimate FLOAT DEFAULT 0.0,
                    user_feedback INTEGER CHECK (user_feedback >= 1 AND user_feedback <= 5)
                )
            """)

            # Document processing logs table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS document_processing_logs (
                    log_id VARCHAR(255) PRIMARY KEY,
                    document_id VARCHAR(255) NOT NULL,
                    session_id VARCHAR(255),
                    processing_stage VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    processing_time_ms FLOAT,
                    error_details JSONB,
                    metadata JSONB DEFAULT '{}'
                )
            """)

            # Create indexes for better performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_agent_sessions_user_id "
                "ON agent_sessions(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_agent_sessions_agent_type "
                "ON agent_sessions(agent_type)",
                "CREATE INDEX IF NOT EXISTS idx_agent_sessions_created_at "
                "ON agent_sessions(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_agent_sessions_status " "ON agent_sessions(status)",
                "CREATE INDEX IF NOT EXISTS idx_agent_metrics_session_id "
                "ON agent_metrics(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_agent_metrics_agent_type "
                "ON agent_metrics(agent_type)",
                "CREATE INDEX IF NOT EXISTS idx_agent_metrics_timestamp "
                "ON agent_metrics(request_timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_agent_metrics_success " "ON agent_metrics(success)",
                "CREATE INDEX IF NOT EXISTS idx_doc_logs_document_id "
                "ON document_processing_logs(document_id)",
                "CREATE INDEX IF NOT EXISTS idx_doc_logs_session_id "
                "ON document_processing_logs(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_doc_logs_stage "
                "ON document_processing_logs(processing_stage)",
                "CREATE INDEX IF NOT EXISTS idx_doc_logs_timestamp "
                "ON document_processing_logs(timestamp)",
            ]

            for index_sql in indexes:
                try:
                    await conn.execute(index_sql)
                except Exception as e:
                    logger.warning(f"Index creation failed: {e}")

    # Session Management
    async def create_session(self, session: AgentSession) -> bool:
        """Create a new agent session."""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO agent_sessions 
                    (session_id, user_id, agent_type, created_at, updated_at, 
                     metadata, message_count, total_tokens, avg_response_time, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                    session.session_id,
                    session.user_id,
                    session.agent_type,
                    session.created_at,
                    session.updated_at,
                    json.dumps(session.metadata),
                    session.message_count,
                    session.total_tokens,
                    session.avg_response_time,
                    session.status,
                )

                logger.info(f"Created session {session.session_id} for agent {session.agent_type}")
                return True

            except Exception as e:
                logger.error(f"Failed to create session {session.session_id}: {e}")
                return False

    async def get_session(self, session_id: str) -> AgentSession | None:
        """Get session by ID."""
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM agent_sessions WHERE session_id = $1
                """,
                    session_id,
                )

                if row:
                    return AgentSession(
                        session_id=row["session_id"],
                        user_id=row["user_id"],
                        agent_type=row["agent_type"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        metadata=row["metadata"],
                        message_count=row["message_count"],
                        total_tokens=row["total_tokens"],
                        avg_response_time=row["avg_response_time"],
                        status=row["status"],
                    )
                return None

            except Exception as e:
                logger.error(f"Failed to get session {session_id}: {e}")
                return None

    async def update_session_metrics(
        self,
        session_id: str,
        message_count_delta: int = 1,
        tokens_delta: int = 0,
        response_time: float = 0.0,
    ) -> bool:
        """Update session metrics incrementally."""
        async with self.pool.acquire() as conn:
            try:
                # Calculate new average response time
                await conn.execute(
                    """
                    UPDATE agent_sessions 
                    SET message_count = message_count + $1,
                        total_tokens = total_tokens + $2,
                        avg_response_time = (avg_response_time * message_count + $3) / 
                            (message_count + $1),
                        updated_at = NOW()
                    WHERE session_id = $4
                """,
                    message_count_delta,
                    tokens_delta,
                    response_time,
                    session_id,
                )

                return True

            except Exception as e:
                logger.error(f"Failed to update session metrics {session_id}: {e}")
                return False

    async def list_sessions(
        self, user_id: str = None, agent_type: str = None, status: str = None, limit: int = 50
    ) -> list[AgentSession]:
        """List sessions with optional filters."""
        async with self.pool.acquire() as conn:
            try:
                conditions = []
                params = []
                param_count = 0

                if user_id:
                    param_count += 1
                    conditions.append(f"user_id = ${param_count}")
                    params.append(user_id)

                if agent_type:
                    param_count += 1
                    conditions.append(f"agent_type = ${param_count}")
                    params.append(agent_type)

                if status:
                    param_count += 1
                    conditions.append(f"status = ${param_count}")
                    params.append(status)

                where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

                param_count += 1
                params.append(limit)

                query = f"""
                    SELECT * FROM agent_sessions 
                    {where_clause}
                    ORDER BY updated_at DESC 
                    LIMIT ${param_count}
                """

                rows = await conn.fetch(query, *params)

                return [
                    AgentSession(
                        session_id=row["session_id"],
                        user_id=row["user_id"],
                        agent_type=row["agent_type"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        metadata=row["metadata"],
                        message_count=row["message_count"],
                        total_tokens=row["total_tokens"],
                        avg_response_time=row["avg_response_time"],
                        status=row["status"],
                    )
                    for row in rows
                ]

            except Exception as e:
                logger.error(f"Failed to list sessions: {e}")
                return []

    # Metrics Management
    async def record_metric(self, metric: AgentMetrics) -> bool:
        """Record an agent performance metric."""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO agent_metrics 
                    (metric_id, session_id, agent_type, endpoint, request_timestamp,
                     response_time_ms, token_count, success, error_message,
                     model_used, cost_estimate, user_feedback)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """,
                    metric.metric_id,
                    metric.session_id,
                    metric.agent_type,
                    metric.endpoint,
                    metric.request_timestamp,
                    metric.response_time_ms,
                    metric.token_count,
                    metric.success,
                    metric.error_message,
                    metric.model_used,
                    metric.cost_estimate,
                    metric.user_feedback,
                )

                return True

            except Exception as e:
                logger.error(f"Failed to record metric {metric.metric_id}: {e}")
                return False

    async def get_agent_performance_stats(
        self, agent_type: str = None, time_range_hours: int = 24
    ) -> dict[str, Any]:
        """Get performance statistics for agents."""
        async with self.pool.acquire() as conn:
            try:
                conditions = [f"request_timestamp > NOW() - INTERVAL '{time_range_hours} hours'"]
                params = []

                if agent_type:
                    conditions.append("agent_type = $1")
                    params.append(agent_type)

                where_clause = "WHERE " + " AND ".join(conditions)

                query = f"""
                    SELECT 
                        agent_type,
                        COUNT(*) as total_requests,
                        AVG(response_time_ms) as avg_response_time,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) 
                            as p95_response_time,
                        SUM(token_count) as total_tokens,
                        AVG(token_count) as avg_tokens,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as success_rate,
                        SUM(cost_estimate) as total_cost,
                        AVG(user_feedback) as avg_feedback
                    FROM agent_metrics 
                    {where_clause}
                    GROUP BY agent_type
                    ORDER BY total_requests DESC
                """

                rows = await conn.fetch(query, *params)

                stats = []
                for row in rows:
                    stats.append(
                        {
                            "agent_type": row["agent_type"],
                            "total_requests": row["total_requests"],
                            "avg_response_time_ms": float(row["avg_response_time"] or 0),
                            "p95_response_time_ms": float(row["p95_response_time"] or 0),
                            "total_tokens": row["total_tokens"] or 0,
                            "avg_tokens": float(row["avg_tokens"] or 0),
                            "success_rate": float(row["success_rate"] or 0),
                            "total_cost": float(row["total_cost"] or 0),
                            "avg_user_feedback": float(row["avg_feedback"] or 0),
                        }
                    )

                return {"time_range_hours": time_range_hours, "agent_stats": stats}

            except Exception as e:
                logger.error(f"Failed to get performance stats: {e}")
                return {}

    # Document Processing Logs
    async def log_document_processing(self, log: DocumentProcessingLog) -> bool:
        """Log document processing event."""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO document_processing_logs 
                    (log_id, document_id, session_id, processing_stage, status,
                     timestamp, processing_time_ms, error_details, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    log.log_id,
                    log.document_id,
                    log.session_id,
                    log.processing_stage,
                    log.status,
                    log.timestamp,
                    log.processing_time_ms,
                    json.dumps(log.error_details) if log.error_details else None,
                    json.dumps(log.metadata),
                )

                return True

            except Exception as e:
                logger.error(f"Failed to log document processing {log.log_id}: {e}")
                return False

    async def get_document_processing_history(
        self, document_id: str
    ) -> list[DocumentProcessingLog]:
        """Get processing history for a document."""
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(
                    """
                    SELECT * FROM document_processing_logs 
                    WHERE document_id = $1 
                    ORDER BY timestamp ASC
                """,
                    document_id,
                )

                return [
                    DocumentProcessingLog(
                        log_id=row["log_id"],
                        document_id=row["document_id"],
                        session_id=row["session_id"],
                        processing_stage=row["processing_stage"],
                        status=row["status"],
                        timestamp=row["timestamp"],
                        processing_time_ms=row["processing_time_ms"],
                        error_details=row["error_details"],
                        metadata=row["metadata"],
                    )
                    for row in rows
                ]

            except Exception as e:
                logger.error(f"Failed to get processing history for {document_id}: {e}")
                return []


# Dependency injection
_postgres_adapter: PostgreSQLAdapter | None = None


async def get_postgres_adapter() -> PostgreSQLAdapter:
    """Get PostgreSQL adapter instance (dependency injection)."""
    global _postgres_adapter

    if _postgres_adapter is None:
        _postgres_adapter = PostgreSQLAdapter()
        await _postgres_adapter.connect()

    return _postgres_adapter


async def close_postgres_adapter() -> None:
    """Close PostgreSQL adapter connection."""
    global _postgres_adapter

    if _postgres_adapter:
        await _postgres_adapter.disconnect()
        _postgres_adapter = None
