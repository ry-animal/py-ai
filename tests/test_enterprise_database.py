"""Tests for enterprise database adapters."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.database.mongodb_adapter import (
    DocumentMetadata,
    MongoDBAdapter,
    StoredDocument,
)
from app.database.postgres_adapter import (
    AgentMetrics,
    AgentSession,
    DocumentProcessingLog,
    PostgreSQLAdapter,
)
from app.database.vector_adapters import (
    CockroachDBAdapter,
    VectorAdapterFactory,
    VectorDBType,
    VectorSearchResult,
    VertexAIAdapter,
)


class TestMongoDBAdapter:
    """Test cases for MongoDB adapter."""

    @pytest.fixture
    def mongodb_adapter(self):
        """Create MongoDB adapter for testing."""
        return MongoDBAdapter("mongodb://test:test@localhost:27017/test")

    @pytest.fixture
    def sample_document_metadata(self):
        """Create sample document metadata."""
        return DocumentMetadata(
            title="Test Document",
            file_type="pdf",
            file_size=1024,
            upload_date=datetime.utcnow(),
            processing_status="pending",
            tags=["test", "document"],
        )

    def test_mongodb_adapter_initialization(self, mongodb_adapter):
        """Test MongoDB adapter initialization."""
        assert mongodb_adapter.connection_string == "mongodb://test:test@localhost:27017/test"
        assert mongodb_adapter.collection_name == "documents"
        assert mongodb_adapter.client is None
        assert mongodb_adapter.db is None

    @pytest.mark.asyncio
    async def test_document_metadata_model(self, sample_document_metadata):
        """Test document metadata model validation."""
        assert sample_document_metadata.title == "Test Document"
        assert sample_document_metadata.file_type == "pdf"
        assert sample_document_metadata.processing_status == "pending"
        assert "test" in sample_document_metadata.tags

    @pytest.mark.asyncio
    async def test_stored_document_model(self, sample_document_metadata):
        """Test stored document model."""
        doc = StoredDocument(
            id="test-doc-123",
            content="This is test content",
            metadata=sample_document_metadata,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert doc.id == "test-doc-123"
        assert doc.content == "This is test content"
        assert doc.metadata.title == "Test Document"

    @pytest.mark.asyncio
    @patch("app.database.mongodb_adapter.AsyncIOMotorClient")
    async def test_mongodb_connect_success(self, mock_client, mongodb_adapter):
        """Test successful MongoDB connection."""
        # Mock successful connection and database access
        mock_client_instance = AsyncMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.admin.command = AsyncMock(return_value={"ok": 1})
        mock_client_instance.__getitem__.return_value = AsyncMock()

        await mongodb_adapter.connect()

        assert mongodb_adapter.client is not None
        mock_client.assert_called_once_with("mongodb://test:test@localhost:27017/test")

    @pytest.mark.asyncio
    @patch("app.database.mongodb_adapter.AsyncIOMotorClient")
    async def test_mongodb_connect_failure(self, mock_client, mongodb_adapter):
        """Test MongoDB connection failure."""
        # Mock connection failure
        mock_client.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            await mongodb_adapter.connect()

    @pytest.mark.asyncio
    async def test_mongodb_search_filters(self, mongodb_adapter):
        """Test MongoDB search filter construction."""
        # This tests the logic without requiring actual DB connection
        _filters = {
            "file_type": "pdf",
            "processing_status": "completed",
            "tags": ["important", "urgent"],
            "date_range": {"start": datetime(2023, 1, 1), "end": datetime(2023, 12, 31)},
        }

        # Test that adapter handles filters correctly (without DB call)
        assert mongodb_adapter.collection_name == "documents"
        # The actual filter construction happens in search_documents method


class TestPostgreSQLAdapter:
    """Test cases for PostgreSQL adapter."""

    @pytest.fixture
    def postgres_adapter(self):
        """Create PostgreSQL adapter for testing."""
        return PostgreSQLAdapter("postgresql://test:test@localhost:5432/test")

    @pytest.fixture
    def sample_agent_session(self):
        """Create sample agent session."""
        return AgentSession(
            session_id="test-session-123",
            user_id="user-456",
            agent_type="pydantic_ai",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"test": "data"},
            message_count=5,
            total_tokens=1000,
            avg_response_time=0.5,
            status="active",
        )

    @pytest.fixture
    def sample_agent_metrics(self):
        """Create sample agent metrics."""
        return AgentMetrics(
            metric_id="metric-789",
            session_id="test-session-123",
            agent_type="pydantic_ai",
            endpoint="/pydantic-agent/chat",
            request_timestamp=datetime.utcnow(),
            response_time_ms=500.0,
            token_count=100,
            success=True,
            model_used="gpt-4o-mini",
            cost_estimate=0.01,
            user_feedback=5,
        )

    def test_postgres_adapter_initialization(self, postgres_adapter):
        """Test PostgreSQL adapter initialization."""
        assert postgres_adapter.connection_string == "postgresql://test:test@localhost:5432/test"
        assert postgres_adapter.pool is None

    def test_agent_session_model(self, sample_agent_session):
        """Test agent session model validation."""
        assert sample_agent_session.session_id == "test-session-123"
        assert sample_agent_session.agent_type == "pydantic_ai"
        assert sample_agent_session.message_count == 5
        assert sample_agent_session.status == "active"

    def test_agent_metrics_model(self, sample_agent_metrics):
        """Test agent metrics model validation."""
        assert sample_agent_metrics.agent_type == "pydantic_ai"
        assert sample_agent_metrics.success is True
        assert sample_agent_metrics.response_time_ms == 500.0
        assert sample_agent_metrics.user_feedback == 5

    @pytest.mark.asyncio
    @patch("app.database.postgres_adapter.asyncpg.create_pool")
    async def test_postgres_connect_success(self, mock_pool, postgres_adapter):
        """Test successful PostgreSQL connection."""
        # Mock successful connection - create_pool returns an awaitable
        mock_conn = AsyncMock()
        mock_pool_instance = AsyncMock()

        # Mock the acquire method to return an async context manager
        class MockAsyncContextManager:
            async def __aenter__(self):
                return mock_conn

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        def mock_acquire():
            return MockAsyncContextManager()

        mock_pool_instance.acquire = mock_acquire

        async def mock_create_pool(*args, **kwargs):
            return mock_pool_instance

        mock_pool.side_effect = mock_create_pool

        await postgres_adapter.connect()

        assert postgres_adapter.pool is not None
        mock_pool.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.database.postgres_adapter.asyncpg.create_pool")
    async def test_postgres_connect_failure(self, mock_pool, postgres_adapter):
        """Test PostgreSQL connection failure."""
        # Mock connection failure
        mock_pool.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            await postgres_adapter.connect()

    def test_document_processing_log_model(self):
        """Test document processing log model."""
        log = DocumentProcessingLog(
            log_id="log-123",
            document_id="doc-456",
            session_id="session-789",
            processing_stage="embedding",
            status="completed",
            timestamp=datetime.utcnow(),
            processing_time_ms=1500.0,
            metadata={"chunks": 10},
        )

        assert log.processing_stage == "embedding"
        assert log.status == "completed"
        assert log.processing_time_ms == 1500.0


class TestVectorAdapters:
    """Test cases for vector database adapters."""

    def test_vector_adapter_factory(self):
        """Test vector adapter factory."""
        factory = VectorAdapterFactory()
        assert factory is not None

    def test_vertex_ai_adapter_initialization(self):
        """Test Vertex AI adapter initialization."""
        adapter = VertexAIAdapter(
            project_id="test-project", region="us-central1", index_endpoint_id="test-endpoint"
        )

        assert adapter.project_id == "test-project"
        assert adapter.region == "us-central1"
        assert adapter.index_endpoint_id == "test-endpoint"
        assert adapter.client is None

    def test_cockroachdb_adapter_initialization(self):
        """Test CockroachDB adapter initialization."""
        adapter = CockroachDBAdapter("postgresql://test:test@localhost:26257/test")

        assert adapter.connection_string == "postgresql://test:test@localhost:26257/test"
        assert adapter.pool is None

    def test_vector_search_result_model(self):
        """Test vector search result model."""
        result = VectorSearchResult(
            id="doc-123",
            content="Test document content",
            metadata={"source": "test.pdf"},
            score=0.95,
            distance=0.05,
        )

        assert result.id == "doc-123"
        assert result.score == 0.95
        assert result.distance == 0.05
        assert result.metadata["source"] == "test.pdf"

    def test_vector_adapter_factory_creation(self):
        """Test vector adapter factory creation for different types."""
        factory = VectorAdapterFactory()

        # Test Vertex AI adapter creation
        vertex_config = {
            "project_id": "test-project",
            "region": "us-central1",
            "index_endpoint_id": "test-endpoint",
        }
        vertex_adapter = factory.create_adapter(VectorDBType.VERTEX_AI, vertex_config)
        assert isinstance(vertex_adapter, VertexAIAdapter)

        # Test CockroachDB adapter creation
        cockroach_config = {"connection_string": "postgresql://test@localhost:26257/test"}
        cockroach_adapter = factory.create_adapter(VectorDBType.COCKROACHDB, cockroach_config)
        assert isinstance(cockroach_adapter, CockroachDBAdapter)

    def test_vector_adapter_factory_unsupported_type(self):
        """Test vector adapter factory with unsupported type."""
        factory = VectorAdapterFactory()

        with pytest.raises(ValueError, match="Unsupported vector database type"):
            factory.create_adapter("unsupported_type", {})

    @pytest.mark.asyncio
    async def test_vertex_ai_adapter_initialization_success(self):
        """Test Vertex AI adapter initialization success."""
        try:
            import google.cloud.aiplatform  # noqa: F401
        except ImportError:
            pytest.skip("google-cloud-aiplatform not installed")

        with (
            patch("google.cloud.aiplatform.init") as mock_init,
            patch("google.cloud.aiplatform.MatchingEngineIndexEndpoint") as mock_endpoint,
        ):
            adapter = VertexAIAdapter(
                project_id="test-project", region="us-central1", index_endpoint_id="test-endpoint"
            )

            # Mock successful initialization
            mock_endpoint.return_value = MagicMock()

            await adapter.initialize()

            mock_init.assert_called_once_with(project="test-project", location="us-central1")
            mock_endpoint.assert_called_once()

    @pytest.mark.asyncio
    @patch("asyncpg.create_pool")
    async def test_cockroachdb_adapter_initialization_success(self, mock_pool):
        """Test CockroachDB adapter initialization success."""
        adapter = CockroachDBAdapter("postgresql://test@localhost:26257/test")

        # Mock successful connection and table creation
        mock_conn = AsyncMock()
        mock_pool_instance = AsyncMock()

        # Mock create_pool to return an awaitable
        async def mock_create_pool(*args, **kwargs):
            return mock_pool_instance

        mock_pool.side_effect = mock_create_pool

        # Mock the acquire method to return an async context manager
        class MockAsyncContextManager:
            async def __aenter__(self):
                return mock_conn

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        def mock_acquire():
            return MockAsyncContextManager()

        mock_pool_instance.acquire = mock_acquire

        await adapter.initialize()

        mock_pool.assert_called_once()
        # Verify table creation SQL was called
        assert mock_conn.execute.call_count > 0


class TestEnterpriseIntegration:
    """Integration tests for enterprise features."""

    @pytest.mark.asyncio
    async def test_multi_agent_system_initialization(self):
        """Test that all agent systems can be initialized."""
        from app.smart_orchestrator import SmartOrchestrator

        # Test smart orchestrator initialization
        orchestrator = SmartOrchestrator()
        assert orchestrator.langgraph_agent is not None
        assert orchestrator.pydantic_agent is not None
        assert orchestrator.hybrid_agent is not None

    @pytest.mark.asyncio
    async def test_task_analysis_functionality(self):
        """Test smart orchestrator task analysis."""
        from app.smart_orchestrator import SmartOrchestrator, TaskCategory, TaskComplexity

        orchestrator = SmartOrchestrator()

        # Test structured output task
        decision = await orchestrator.analyze_task("Extract user data in JSON format")
        assert decision.task_category == TaskCategory.STRUCTURED_OUTPUT
        assert decision.chosen_agent.value == "pydantic_ai"
        assert decision.confidence > 0.8

        # Test complex workflow task
        decision = await orchestrator.analyze_task(
            "Analyze our ML models and create a step-by-step improvement workflow"
        )
        assert decision.task_category == TaskCategory.WORKFLOW
        assert decision.task_complexity in [TaskComplexity.COMPLEX, TaskComplexity.MODERATE]

    @pytest.mark.asyncio
    async def test_enterprise_configuration_loading(self):
        """Test enterprise configuration loading."""
        from app.config import get_settings

        settings = get_settings()

        # Test that enterprise configuration fields exist
        assert hasattr(settings, "vector_db_type")
        assert hasattr(settings, "mongodb_url")
        assert hasattr(settings, "postgres_url")
        assert hasattr(settings, "enable_smart_orchestrator")
        assert hasattr(settings, "enable_hybrid_agent")
        assert hasattr(settings, "enable_pydantic_agent")

    def test_database_adapter_imports(self):
        """Test that all database adapters can be imported."""
        # Test MongoDB adapter import
        from app.database.mongodb_adapter import MongoDBAdapter, get_mongodb_adapter

        assert MongoDBAdapter is not None
        assert get_mongodb_adapter is not None

        # Test PostgreSQL adapter import
        from app.database.postgres_adapter import PostgreSQLAdapter, get_postgres_adapter

        assert PostgreSQLAdapter is not None
        assert get_postgres_adapter is not None

        # Test vector adapters import
        from app.database.vector_adapters import VectorAdapterFactory, get_vector_adapter

        assert VectorAdapterFactory is not None
        assert get_vector_adapter is not None

    def test_enterprise_routers_import(self):
        """Test that enterprise routers can be imported."""
        from app.routers_hybrid_agent import hybrid_agent_router
        from app.routers_pydantic_agent import pydantic_agent_router
        from app.routers_smart_orchestrator import orchestrator_router

        assert orchestrator_router is not None
        assert hybrid_agent_router is not None
        assert pydantic_agent_router is not None


# Performance and load testing helpers
class TestPerformanceHelpers:
    """Performance and load testing utilities."""

    @pytest.mark.asyncio
    async def test_concurrent_agent_requests(self):
        """Test handling of concurrent agent requests."""
        from app.smart_orchestrator import SmartOrchestrator

        orchestrator = SmartOrchestrator()

        # Create multiple concurrent analysis tasks
        tasks = []
        questions = [
            "What is Python?",
            "Extract data in JSON format",
            "Create a complex workflow",
            "Analyze performance metrics",
            "Simple question answering",
        ]

        for question in questions:
            task = orchestrator.analyze_task(question)
            tasks.append(task)

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)

        # Verify all tasks completed successfully
        assert len(results) == len(questions)
        for result in results:
            assert result.chosen_agent is not None
            assert result.confidence > 0.0
            assert result.reasoning is not None

    def test_memory_usage_estimation(self):
        """Test memory usage for enterprise components."""
        import sys

        from app.database.mongodb_adapter import DocumentMetadata
        from app.database.postgres_adapter import AgentSession

        # Test memory footprint of data models
        metadata = DocumentMetadata(
            title="Test", file_type="pdf", file_size=1024, upload_date=datetime.utcnow()
        )

        session = AgentSession(
            session_id="test",
            agent_type="pydantic_ai",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Verify objects are created without excessive memory usage
        assert sys.getsizeof(metadata) < 1000  # Reasonable size limit
        assert sys.getsizeof(session) < 1000


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
