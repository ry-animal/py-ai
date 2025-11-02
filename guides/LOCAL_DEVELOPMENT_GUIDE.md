# Local Development Guide

Complete guide for setting up and using the py-ai multi-agent platform locally.

## 🎯 Overview

Local development setup provides:
- All 4 agent architectures (Smart Orchestrator, Pydantic-AI, Hybrid, LangGraph)
- ChromaDB for vector storage (no cloud dependencies)
- Redis for agent memory and caching
- Docker Compose for easy orchestration
- Hot reloading for development
- Cost: $0 (only API usage charges)

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites

```bash
# Required software
- Docker Desktop (4.0+)
- Python 3.11+
- uv (Python package manager)
- Git

# Check prerequisites
docker --version
python --version
uv --version
```

### 2. Clone and Setup

```bash
# Clone repository
git clone https://github.com/your-username/py-ai.git
cd py-ai

# Install dependencies
make setup

# Or manually:
uv sync
uv run pre-commit install
```

### 3. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

**Required Environment Variables:**
```ini
# API Keys (Required)
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-openai-key-here  # Optional but recommended

# Optional Features
TAVILY_API_KEY=your-tavily-key  # For web search
STREAMING_ENABLED=true
MODEL_NAME=gpt-4o-mini
CLAUDE_MODEL=claude-3-5-sonnet-latest

# Local Development (Default values)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Performance Settings
MAX_REQUEST_BODY_BYTES=10485760  # 10MB
RATE_LIMIT_REQUESTS_PER_WINDOW=120
RATE_LIMIT_WINDOW_SECONDS=60

# Vector Database (Local)
VECTOR_DB_TYPE=chroma
RAG_STORE_PATH=./.rag_store
```

### 4. Start the Platform

```bash
# Start everything with Docker Compose
docker compose up --build

# Or start in background
docker compose up -d --build

# Check status
docker compose ps
```

### 5. Verify Installation

```bash
# Health check
curl http://localhost:8010/health

# Test smart orchestrator
curl http://localhost:8010/smart/status

# Test all 4 agents
curl http://localhost:8010/smart/agents/comparison
```

## 🧪 Development Workflow

### Daily Development Commands

```bash
# Start development environment
make dev-start    # docker compose up -d

# View logs
make dev-logs     # docker compose logs -f

# Restart services
make dev-restart  # docker compose restart

# Stop everything
make dev-stop     # docker compose down

# Clean rebuild
make dev-clean    # docker compose down -v && docker compose up --build
```

### Code Changes and Hot Reloading

```bash
# For API changes (auto-reloads)
# Edit files in src/app/
# Changes are automatically reflected (volume mounted)

# For dependency changes
docker compose build api worker
docker compose up -d api worker

# For tests
uv run pytest tests/ -v
```

### Local Testing Commands

```bash
# Quick workflow validation
source scripts/py-dev-workflow.sh  # comprehensive end-to-end test
# ✅ Runs: health check → agent availability → smart routing → chat

# Test all agent architectures
make test-all-agents

# Test specific components
make test          # Run all tests
make test-unit     # Unit tests only
make test-integration  # Integration tests only

# Performance testing
make test-performance

# Manual agent testing
make demo-integration
```

## 🤖 Multi-Agent Development

### Testing Individual Agents

```bash
# 1. Smart Orchestrator (Intelligent Routing)
curl "http://localhost:8010/smart/chat?q=What%20is%20Python?"

# 2. Pydantic-AI Agent (Type-Safe)
curl "http://localhost:8010/pydantic-agent/chat?q=Extract%20data%20in%20JSON"

# 3. Hybrid Agent (Best of Both Worlds)
curl "http://localhost:8010/hybrid-agent/chat?q=Create%20a%20workflow"

# 4. LangGraph Agent (Complex Workflows)
curl "http://localhost:8010/agent/chat?q=Analyze%20this%20process"
```

### Agent Development Patterns

```python
# Example: Adding a new tool to Pydantic-AI agent
# File: src/app/pydantic_agent_service.py

from pydantic_ai import Agent
from pydantic import BaseModel

class NewToolOutput(BaseModel):
    result: str
    confidence: float

@agent.tool
async def new_tool(ctx: RunContext, query: str) -> NewToolOutput:
    """Your new tool implementation."""
    return NewToolOutput(
        result="Tool result",
        confidence=0.95
    )
```

### Debugging Agent Behavior

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Check agent selection logic
curl -X POST http://localhost:8010/smart/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "Your test question"}' | jq '.'

# View agent capabilities
curl http://localhost:8010/pydantic-agent/debug/capabilities

# Monitor agent performance
curl http://localhost:8010/smart/agents/comparison | jq '.performance'
```

## 📊 Document Management (RAG)

### Local Document Testing

```bash
# Upload test documents
curl -X POST http://localhost:8010/docs/upload \
  -F "file=@demo_docs/company_handbook.md"

# List documents
curl http://localhost:8010/docs/ | jq '.'

# Test RAG with documents
curl "http://localhost:8010/chat/?q=What%20are%20the%20company%20values?"

# Reload RAG index
curl -X POST http://localhost:8010/rag/reload \
  -H 'Content-Type: application/json' \
  -d '[["1","Your test content here"]]'
```

### ChromaDB Management

```bash
# View ChromaDB data directory
ls -la .rag_store/

# Reset vector database
rm -rf .rag_store/
docker compose restart api

# Backup vector database
tar -czf rag_backup_$(date +%Y%m%d).tar.gz .rag_store/
```

## 🔍 Development Tools

### Built-in Development Endpoints

```bash
# API Documentation
open http://localhost:8010/docs

# Health and Status
curl http://localhost:8010/health
curl http://localhost:8010/ready

# Agent Status Pages
curl http://localhost:8010/smart/status | jq '.'
curl http://localhost:8010/pydantic-agent/status | jq '.'
curl http://localhost:8010/hybrid-agent/status | jq '.'

# Performance Metrics
curl http://localhost:8010/metrics  # If implemented
```

### Log Analysis

```bash
# Follow API logs
docker compose logs -f api

# Follow worker logs
docker compose logs -f worker

# Follow Redis logs
docker compose logs -f redis

# Search logs for errors
docker compose logs api | grep -i error

# Export logs for analysis
docker compose logs --no-color api > api_logs.txt
```

### Performance Monitoring

```bash
# Monitor container resources
docker stats

# Monitor specific container
docker stats py-ai-api-1

# Check memory usage
docker exec py-ai-api-1 cat /proc/meminfo

# Network monitoring
docker network ls
docker network inspect py-ai_default
```

## 🧩 Development Tasks

### Adding New Agent Features

```python
# 1. Create new tool in src/app/tools/
# File: src/app/tools/new_tool.py

async def new_tool_function(query: str) -> dict:
    """Implement your new tool logic."""
    return {"result": "tool output"}

# 2. Register with agent
# File: src/app/pydantic_agent_service.py

from .tools.new_tool import new_tool_function

@agent.tool
async def new_tool(ctx: RunContext, query: str) -> dict:
    return await new_tool_function(query)
```

### Testing New Features

```bash
# Test new endpoint
curl -X POST http://localhost:8010/your-new-endpoint \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# Run specific tests
uv run pytest tests/test_your_feature.py -v

# Integration testing
make test-integration
```

### Database Development

```bash
# Connect to Redis
docker exec -it py-ai-redis-1 redis-cli

# Check Redis data
KEYS *
GET agent_memory:*

# Monitor Redis operations
MONITOR

# Export Redis data
docker exec py-ai-redis-1 redis-cli --rdb /data/dump.rdb
```

## 🚨 Troubleshooting

### Common Issues

**1. Docker Build Failures**
```bash
# Clean Docker cache
docker system prune -a

# Rebuild from scratch
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

**2. Port Conflicts**
```bash
# Check what's using port 8010
lsof -i :8010

# Kill process on port
kill -9 $(lsof -t -i:8010)

# Use different ports in docker-compose.yml
```

**3. Memory Issues**
```bash
# Increase Docker memory limit
# Docker Desktop > Settings > Resources > Memory

# Monitor memory usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

**4. API Key Issues**
```bash
# Verify environment variables
docker exec py-ai-api-1 env | grep API_KEY

# Check logs for auth errors
docker compose logs api | grep -i "api key\|auth\|permission"
```

### Debug Mode

```bash
# Start in debug mode
docker compose -f docker-compose.yml -f docker-compose.debug.yml up

# Enable verbose logging
export LOG_LEVEL=DEBUG
export PYTHONPATH=/app/src
docker compose up --build
```

### Performance Debugging

```bash
# Profile API performance
curl -w "@curl-format.txt" http://localhost:8010/smart/chat?q=test

# Create curl-format.txt:
cat > curl-format.txt << 'EOF'
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
EOF
```

## 📝 Development Workflows

### Feature Development Cycle

```bash
# 1. Create feature branch
git checkout -b feature/new-agent-capability

# 2. Start development environment
make dev-start

# 3. Make changes and test
# Edit code in src/app/
curl http://localhost:8010/your-new-endpoint

# 4. Run tests
make test

# 5. Commit and push
git add .
git commit -m "Add new agent capability"
git push origin feature/new-agent-capability
```

### Testing Workflow

```bash
# 1. Unit tests during development
uv run pytest tests/test_specific.py -v -s

# 2. Integration tests before commit
make test-integration

# 3. Full test suite before PR
make test-all

# 4. Performance tests for significant changes
make test-performance
```

### Release Workflow

```bash
# 1. Prepare release
git checkout main
git pull origin main

# 2. Test everything locally
make test-all
make validate-enterprise

# 3. Build and tag
docker build -t py-ai:v1.0.0 .
git tag v1.0.0

# 4. Deploy to staging
./scripts/deploy-staging.sh

# 5. Deploy to production (when ready)
./scripts/deploy-production.sh
```

## 📋 Local Development Checklist

- [ ] Docker Desktop running
- [ ] Environment variables configured (.env)
- [ ] API keys valid and accessible
- [ ] All containers healthy (`docker compose ps`)
- [ ] Health endpoints responding
- [ ] All 4 agents operational
- [ ] Tests passing (`make test`)
- [ ] Documentation updated
- [ ] Git workflow established

## 🎯 Next Steps

1. **Explore agent capabilities** using the test commands
2. **Develop new features** using the provided patterns
3. **Test thoroughly** with the local setup
4. **Deploy to staging** when ready for broader testing
5. **Scale to production** using the enterprise guide

---

🚀 **Your local development environment is ready for multi-agent AI development!**

Access your local API at: http://localhost:8010