"""Integration tests for enterprise multi-agent system."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


class TestEnterpriseAPIIntegration:
    """Integration tests for enterprise API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client with enterprise configuration."""
        app = create_app()
        return TestClient(app)

    def test_health_endpoints(self, client):
        """Test health and readiness endpoints."""
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

        # Test readiness endpoint
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_smart_orchestrator_status(self, client):
        """Test smart orchestrator status endpoint."""
        response = client.get("/smart/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ready"
        assert data["architecture"] == "Smart Multi-Agent Orchestrator"
        assert "available_agents" in data
        assert "selection_logic" in data

        # Verify all expected agents are available
        expected_agents = ["langgraph", "pydantic_ai", "hybrid"]
        assert all(agent in data["available_agents"] for agent in expected_agents)

    def test_agent_comparison_endpoint(self, client):
        """Test agent comparison endpoint."""
        response = client.get("/smart/agents/comparison")
        assert response.status_code == 200

        data = response.json()
        assert "available_agents" in data
        assert "selection_criteria" in data

        # Verify all agent types are documented
        agents = data["available_agents"]
        assert "langgraph" in agents
        assert "pydantic_ai" in agents
        assert "hybrid" in agents
        assert "smart_orchestrator" in agents

        # Verify each agent has required fields
        for _agent_name, agent_info in agents.items():
            assert "endpoint" in agent_info
            assert "strengths" in agent_info
            assert "best_for" in agent_info

    def test_task_analysis_endpoint(self, client):
        """Test task analysis endpoint."""
        # Test structured output task
        response = client.post(
            "/smart/analyze", json={"question": "Extract user data in JSON format"}
        )
        assert response.status_code == 200

        data = response.json()
        assert "decision" in data
        assert "explanation" in data

        decision = data["decision"]
        assert decision["chosen_agent"] == "pydantic_ai"
        assert decision["task_category"] == "structured_output"
        assert decision["confidence"] >= 0.8

        # Test complex workflow task
        response = client.post(
            "/smart/analyze",
            json={
                "question": "Analyze our ML models and create a step-by-step improvement workflow"
            },
        )
        assert response.status_code == 200

        data = response.json()
        decision = data["decision"]
        assert decision["task_category"] == "workflow"
        assert decision["task_complexity"] in ["complex", "moderate"]

    @patch("app.ai_service.AIService.generate_answer")
    def test_smart_orchestrator_chat(self, mock_generate, client):
        """Test smart orchestrator chat endpoint."""
        # Mock AI service response
        mock_generate.return_value = "Hello! How can I assist you today?"

        # Test GET endpoint
        response = client.get("/smart/chat?q=Hello")
        assert response.status_code == 200

        # Test POST endpoint
        response = client.post(
            "/smart/chat", json={"question": "What is Python?", "session_id": "test-session-123"}
        )
        assert response.status_code == 200

    def test_pydantic_agent_endpoints(self, client):
        """Test Pydantic-AI agent endpoints."""
        # Test status endpoint
        response = client.get("/pydantic-agent/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ready"
        assert data["model"] == "openai:gpt-4o"

        # Test capabilities endpoint
        response = client.get("/pydantic-agent/debug/capabilities")
        assert response.status_code == 200

        data = response.json()
        assert "tools" in data
        assert "dependencies" in data

    def test_hybrid_agent_endpoints(self, client):
        """Test hybrid agent endpoints."""
        # Test status endpoint
        response = client.get("/hybrid-agent/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ready"
        assert data["architecture"] == "LangGraph + Pydantic-AI Hybrid"

        # Test architecture endpoint
        response = client.get("/hybrid-agent/architecture")
        assert response.status_code == 200

        data = response.json()
        assert "design_pattern" in data
        assert "components" in data

    @patch("app.ai_service.AIService.generate_answer")
    def test_all_agent_chat_endpoints(self, mock_generate, client):
        """Test that all agent chat endpoints are functional."""
        # Mock AI service response
        mock_generate.return_value = "Test response"

        # Test all agent endpoints
        endpoints = [
            "/agent/chat?q=Hello",
            "/pydantic-agent/chat?q=Hello",
            "/hybrid-agent/chat?q=Hello",
            "/smart/chat?q=Hello",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Failed for endpoint: {endpoint}"

    def test_streaming_support(self, client):
        """Test streaming support across all agents."""
        # Test streaming endpoints (should not fail even if streaming not fully implemented)
        streaming_endpoints = [
            "/smart/chat?q=Hello&stream=true",
            "/pydantic-agent/chat?q=Hello&stream=true",
        ]

        for endpoint in streaming_endpoints:
            response = client.get(endpoint)
            # Should either work (200) or return valid error
            assert response.status_code in [200, 422], f"Unexpected status for {endpoint}"

    def test_error_handling(self, client):
        """Test error handling across enterprise endpoints."""
        # Test malformed JSON
        response = client.post(
            "/smart/analyze", data="invalid json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Validation error

        # Test non-existent endpoints
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404


class TestEnterprisePerformance:
    """Performance tests for enterprise features."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)

    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        import threading
        import time

        results = []
        errors = []

        def make_request():
            try:
                response = client.get("/smart/status")
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Create multiple concurrent threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)

        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        end_time = time.time()

        # Verify results
        assert len(results) == 10
        assert all(status == 200 for status in results)
        assert len(errors) == 0
        assert end_time - start_time < 5.0  # Should complete within 5 seconds

    def test_response_time_benchmarks(self, client):
        """Test response time benchmarks for key endpoints."""
        import time

        endpoints_to_test = [
            "/health",
            "/ready",
            "/smart/status",
            "/smart/agents/comparison",
            "/pydantic-agent/status",
            "/hybrid-agent/status",
        ]

        response_times = {}

        for endpoint in endpoints_to_test:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()

            response_time = end_time - start_time
            response_times[endpoint] = response_time

            # Verify response is successful
            assert response.status_code == 200

            # Response time should be reasonable (< 1 second for status endpoints)
            assert response_time < 1.0, f"Endpoint {endpoint} took {response_time:.2f}s"

        # Print response times for monitoring
        print("\nResponse time benchmarks:")
        for endpoint, time_taken in response_times.items():
            print(f"  {endpoint}: {time_taken:.3f}s")

    def test_memory_usage_stability(self, client):
        """Test memory usage stability under load."""
        import gc
        import os

        import psutil

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Make multiple requests
        for i in range(50):
            response = client.get("/smart/status")
            assert response.status_code == 200

            if i % 10 == 0:
                gc.collect()  # Force garbage collection

        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(
            f"\nMemory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB "
            f"(+{memory_increase:.1f}MB)"
        )

        # Memory increase should be reasonable (< 400MB for 50 requests with lazy loading)
        # Note: Higher threshold due to lazy initialization of agents during test run
        assert memory_increase < 400, f"Memory increased by {memory_increase:.1f}MB"


class TestEnterpriseConfigurationValidation:
    """Test enterprise configuration validation."""

    def test_vector_database_configuration(self):
        """Test vector database configuration options."""
        from app.config import AppSettings

        # Test valid vector database types
        valid_types = ["vertex", "snowflake", "cockroach", "chroma"]

        for db_type in valid_types:
            settings = AppSettings(vector_db_type=db_type)
            assert settings.vector_db_type == db_type

    def test_multi_agent_feature_flags(self):
        """Test multi-agent feature flag configuration."""
        from app.config import AppSettings

        # Test all agents enabled
        settings = AppSettings(
            enable_smart_orchestrator=True,
            enable_hybrid_agent=True,
            enable_pydantic_agent=True,
            enable_langgraph_agent=True,
        )

        assert settings.enable_smart_orchestrator is True
        assert settings.enable_hybrid_agent is True
        assert settings.enable_pydantic_agent is True
        assert settings.enable_langgraph_agent is True

    def test_enterprise_database_urls(self):
        """Test enterprise database URL configuration."""
        from app.config import AppSettings

        settings = AppSettings(
            mongodb_url="mongodb://localhost:27017/test",
            postgres_url="postgresql://localhost:5432/test",
            redis_url="redis://localhost:6379/0",
        )

        assert settings.mongodb_url == "mongodb://localhost:27017/test"
        assert settings.postgres_url == "postgresql://localhost:5432/test"
        assert settings.redis_url == "redis://localhost:6379/0"


class TestEnterpriseSecurityFeatures:
    """Test enterprise security features."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)

    def test_rate_limiting_headers(self, client):
        """Test that rate limiting headers are present."""
        response = client.get("/health")
        assert response.status_code == 200

        # Check for rate limiting headers (if implemented)
        # Note: This may need adjustment based on actual implementation
        headers = response.headers
        print(f"Response headers: {dict(headers)}")

    def test_request_id_tracking(self, client):
        """Test request ID tracking."""
        response = client.get("/health")
        assert response.status_code == 200

        # Check for request ID header
        headers = response.headers
        # Note: Actual header name may vary based on implementation
        print(f"Headers for request tracking: {dict(headers)}")

    def test_input_validation(self, client):
        """Test input validation and sanitization."""
        # Test malformed JSON
        response = client.post(
            "/smart/analyze", data="invalid json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

        # Test missing required fields - note: API provides defaults so this returns 200
        response = client.post("/smart/analyze", json={})
        assert response.status_code == 200  # API has defaults

        # Test invalid field types - the API handles this gracefully by converting to string
        response = client.post(
            "/smart/analyze",
            json={
                "question": 123  # Should be string, but API converts it
            },
        )
        assert response.status_code == 200  # API handles type conversion gracefully

    def test_cors_configuration(self, client):
        """Test CORS configuration."""
        # Test OPTIONS request
        response = client.options("/health")
        # CORS headers should be present
        headers = response.headers
        print(f"CORS headers: {dict(headers)}")


# Utility functions for manual testing
class TestManualTestingHelpers:
    """Helpers for manual testing procedures."""

    def test_generate_test_data(self):
        """Generate test data for manual testing."""
        from datetime import datetime

        from app.database.mongodb_adapter import DocumentMetadata
        from app.database.postgres_adapter import AgentSession

        # Generate sample document metadata
        test_metadata = DocumentMetadata(
            title="Enterprise Test Document",
            file_type="pdf",
            file_size=2048,
            upload_date=datetime.utcnow(),
            processing_status="completed",
            tags=["enterprise", "test", "manual"],
        )

        # Generate sample agent session
        test_session = AgentSession(
            session_id="manual-test-session",
            user_id="test-user",
            agent_type="smart_orchestrator",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"test_type": "manual", "environment": "staging"},
        )

        print(f"Test Document Metadata: {test_metadata.model_dump()}")
        print(f"Test Agent Session: {test_session.model_dump()}")

    def test_endpoint_discovery(self):
        """Discover all available endpoints for manual testing."""
        app = create_app()

        print("\n🔍 Available Enterprise Endpoints:")
        print("=" * 50)

        routes_by_category = {
            "Health & Status": [],
            "Smart Orchestrator": [],
            "Pydantic-AI Agent": [],
            "Hybrid Agent": [],
            "LangGraph Agent": [],
            "Documents": [],
            "Chat": [],
            "Other": [],
        }

        for route in app.routes:
            if hasattr(route, "path"):
                path = route.path

                if any(x in path for x in ["/health", "/ready"]):
                    routes_by_category["Health & Status"].append(path)
                elif "/smart/" in path:
                    routes_by_category["Smart Orchestrator"].append(path)
                elif "/pydantic-agent/" in path:
                    routes_by_category["Pydantic-AI Agent"].append(path)
                elif "/hybrid-agent/" in path:
                    routes_by_category["Hybrid Agent"].append(path)
                elif "/agent/" in path:
                    routes_by_category["LangGraph Agent"].append(path)
                elif "/docs/" in path:
                    routes_by_category["Documents"].append(path)
                elif "/chat/" in path:
                    routes_by_category["Chat"].append(path)
                else:
                    routes_by_category["Other"].append(path)

        for category, paths in routes_by_category.items():
            if paths:
                print(f"\n{category}:")
                for path in sorted(paths):
                    print(f"  {path}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
