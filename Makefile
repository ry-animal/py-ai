.PHONY: run test lint format eval setup py-dev-workflow py-test-httpie py-aliases

API_BASE_URL ?= http://127.0.0.1:8010

run:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest -q

lint:
	uv run ruff check .

format:
	uv run ruff format .

eval:
	API_BASE_URL=$(API_BASE_URL) uv run python scripts/run_evals.py

ragas:
	API_BASE_URL=$(API_BASE_URL) uv run python scripts/run_ragas.py

weval:
	API_BASE_URL=$(API_BASE_URL) uv run python scripts/run_web_evals.py

agent-eval:
	uv run python scripts/run_agent_evals.py

compare-agents:
	uv run python scripts/compare_agents.py

test-hybrid:
	curl -s "http://localhost:8010/hybrid-agent/chat?q=What%20is%20Python?" | python3 -m json.tool

test-smart:
	curl -s "http://localhost:8010/smart/chat?q=What%20is%20Python?" | python3 -m json.tool

test-all-agents:
	@echo "🧪 Testing all agent architectures..."
	@echo "1️⃣ LangGraph Agent:"
	@curl -s "http://localhost:8010/agent/chat?q=What%20is%20Python?" | head -c 100 || echo "❌ Failed"
	@echo "\n\n2️⃣ Pydantic-AI Agent:"
	@curl -s "http://localhost:8010/pydantic-agent/chat?q=What%20is%20Python?" | head -c 100 || echo "❌ Failed"
	@echo "\n\n3️⃣ Hybrid Agent:"
	@curl -s "http://localhost:8010/hybrid-agent/chat?q=What%20is%20Python?" | head -c 100 || echo "❌ Failed"
	@echo "\n\n4️⃣ Smart Orchestrator:"
	@curl -s "http://localhost:8010/smart/chat?q=What%20is%20Python?" | head -c 100 || echo "❌ Failed"
	@echo "\n\n✅ All tests completed!"

agent-status:
	@echo "📊 Agent Status Summary:"
	@echo "• Pydantic-AI: $$(curl -s http://localhost:8010/pydantic-agent/status | python3 -c "import json, sys; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo '❌ Error')"
	@echo "• Hybrid: $$(curl -s http://localhost:8010/hybrid-agent/status | python3 -c "import json, sys; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo '❌ Error')"
	@echo "• Smart: $$(curl -s http://localhost:8010/smart/status | python3 -c "import json, sys; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo '❌ Error')"

demo-integration:
	@echo "🎯 Multi-Agent Integration Demo"
	@echo "=" * 40
	@echo "Testing task-aware routing..."
	@echo "\n📝 Simple Q&A (should route to Pydantic-AI):"
	@curl -s -X POST http://localhost:8010/smart/analyze -H "Content-Type: application/json" -d '{"question": "What is Python?"}' | python3 -c "import json, sys; data=json.load(sys.stdin); print(f'Agent: {data[\"decision\"][\"chosen_agent\"]} | Confidence: {data[\"decision\"][\"confidence\"]:.0%} | Reason: {data[\"decision\"][\"reasoning\"]}')"
	@echo "\n🔧 Complex workflow (should route to LangGraph):"
	@curl -s -X POST http://localhost:8010/smart/analyze -H "Content-Type: application/json" -d '{"question": "Analyze our ML models and create a step-by-step improvement workflow"}' | python3 -c "import json, sys; data=json.load(sys.stdin); print(f'Agent: {data[\"decision\"][\"chosen_agent\"]} | Confidence: {data[\"decision\"][\"confidence\"]:.0%} | Reason: {data[\"decision\"][\"reasoning\"]}')"
	@echo "\n📊 Structured output (should route to Pydantic-AI):"
	@curl -s -X POST http://localhost:8010/smart/analyze -H "Content-Type: application/json" -d '{"question": "Extract user data in JSON format"}' | python3 -c "import json, sys; data=json.load(sys.stdin); print(f'Agent: {data[\"decision\"][\"chosen_agent\"]} | Confidence: {data[\"decision\"][\"confidence\"]:.0%} | Reason: {data[\"decision\"][\"reasoning\"]}')"

worker:
	uv run celery -A app.tasks worker --loglevel=info

# Enterprise Development Commands
setup-enterprise:
	uv add --group enterprise
	uv sync
	uv run pre-commit install || uvx pre-commit install || true

terraform-plan:
	cd terraform/environments/staging && terraform plan

terraform-apply:
	cd terraform/environments/staging && terraform apply

terraform-destroy:
	cd terraform/environments/staging && terraform destroy

# Database testing
test-mongodb:
	@echo "Testing MongoDB connection..."
	uv run python -c "import asyncio; from app.database.mongodb_adapter import get_mongodb_adapter; asyncio.run(get_mongodb_adapter())"

test-postgres:
	@echo "Testing PostgreSQL connection..."
	uv run python -c "import asyncio; from app.database.postgres_adapter import get_postgres_adapter; asyncio.run(get_postgres_adapter())"

test-vector-db:
	@echo "Testing vector database connection..."
	uv run python -c "import asyncio; from app.database.vector_adapters import get_vector_adapter; asyncio.run(get_vector_adapter())"

test-databases:
	@echo "🗄️ Testing all enterprise databases..."
	make test-mongodb
	make test-postgres
	make test-vector-db
	@echo "✅ All database connections tested!"

# Enterprise deployment validation
validate-enterprise:
	@echo "🏢 Validating enterprise deployment..."
	@echo "Testing API health..."
	@curl -f $(API_BASE_URL)/health || echo "❌ Health check failed"
	@echo "\nTesting all agent architectures..."
	make test-all-agents
	@echo "\nTesting enterprise features..."
	@curl -s $(API_BASE_URL)/smart/agents/comparison | head -c 100 || echo "❌ Agent comparison failed"
	@echo "\n✅ Enterprise validation complete!"

setup:
	uv sync
	uv run pre-commit install || uvx pre-commit install || true

# HTTPie Development Commands
py-dev-workflow:
	@echo "🚀 Running development workflow with HTTPie..."
	./scripts/py-dev-workflow.sh

py-test-httpie:
	@echo "🧪 Testing HTTPie integration..."
	@command -v http >/dev/null 2>&1 || { echo "❌ HTTPie not installed. Run: brew install httpie"; exit 1; }
	@echo "✅ HTTPie available"
	http GET localhost:8010/health
	http GET localhost:8010/smart/status

py-aliases:
	@echo "📋 HTTPie aliases available:"
	@echo "source scripts/httpie-aliases.sh"
	@echo ""
	@echo "Then use commands like:"
	@echo "  py-health"
	@echo "  py-status" 
	@echo "  py-chat q=='Hello'"
	@echo "  py-analyze-question 'Your question'"
	@echo ""
	@echo "Run 'py-help' for full command list"

py-context7-demo:
	@echo "📚 Running Context7 integration demo..."
	./scripts/httpie-context7-demo.sh
