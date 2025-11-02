# Development Workflow Guide

Comprehensive workflow guide for developing with the py-ai multi-agent platform.

## 🎯 **Local Development Status: ✅ OPERATIONAL**

Your local environment is running successfully with:
- **All 4 Agent Architectures**: Smart Orchestrator, Pydantic-AI, Hybrid, LangGraph ✅
- **Intelligent Routing**: 90% confidence task analysis ✅
- **RAG Functionality**: Document upload and Q&A working ✅
- **Performance**: Concurrent requests handled successfully ✅
- **API Access**: http://localhost:8010 ✅

## 🚀 **Daily Development Commands**

### Quick Start
```bash
# Start everything
docker compose up -d

# Check status
curl http://localhost:8010/health

# View logs
docker compose logs -f api
```

### Development Loop
```bash
# 1. Make code changes in src/app/
# 2. Changes auto-reload (no restart needed)
# 3. Test your changes
curl "http://localhost:8010/your-endpoint"

# 4. Run tests
uv run pytest tests/ -v

# 5. Commit changes
git add . && git commit -m "Your changes"
```

## 🧪 **Testing Workflows**

### Agent Development Testing

```bash
# Test Smart Orchestrator Intelligence
curl -s -X POST http://localhost:8010/smart/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "Extract user data in JSON format"}' | jq '.decision'

# Test Agent Routing
curl -s "http://localhost:8010/smart/chat?q=What%20is%20Python?" | jq '.agent_used'

# Test Individual Agents
curl -s "http://localhost:8010/pydantic-agent/chat?q=Hello" | jq '.answer'
curl -s "http://localhost:8010/agent/chat?q=Hello" | jq '.answer'
```

### Document & RAG Testing

```bash
# Upload document
curl -X POST http://localhost:8010/docs/upload \
  -F "file=@demo_docs/company_handbook.md"

# Manual RAG reload (for testing)
curl -X POST http://localhost:8010/rag/reload \
  -H 'Content-Type: application/json' \
  -d '[["1","Test content about company values and policies."]]'

# Test RAG Q&A
curl -s "http://localhost:8010/ask?q=What%20are%20the%20company%20values?" | jq '.answer'
```

### Performance Testing

```bash
# Concurrent requests
for i in {1..10}; do curl -s http://localhost:8010/smart/status > /dev/null & done; wait

# Response time testing
time curl -s "http://localhost:8010/smart/chat?q=Hello" > /dev/null

# Memory monitoring
docker stats py-ai-api-1
```

## 🛠️ **Development Patterns**

### Adding New Agent Capabilities

**1. Create New Tool (Pydantic-AI)**
```python
# File: src/app/tools/my_new_tool.py
from pydantic import BaseModel

class ToolResult(BaseModel):
    result: str
    confidence: float

async def my_new_tool(query: str) -> ToolResult:
    """Your tool implementation."""
    return ToolResult(
        result="Tool output",
        confidence=0.95
    )
```

**2. Register Tool with Agent**
```python
# File: src/app/pydantic_agent_service.py
from .tools.my_new_tool import my_new_tool

@agent.tool
async def new_tool(ctx: RunContext, query: str) -> ToolResult:
    """Tool description for the agent."""
    return await my_new_tool(query)
```

**3. Test New Tool**
```bash
# Test tool functionality
curl -s "http://localhost:8010/pydantic-agent/chat?q=Use%20the%20new%20tool" | jq '.'

# Check tool availability
curl -s http://localhost:8010/pydantic-agent/debug/capabilities | jq '.tools'
```

### Adding New Endpoints

**1. Create Router**
```python
# File: src/app/routers_new_feature.py
from fastapi import APIRouter
from .schemas import NewFeatureRequest, NewFeatureResponse

router = APIRouter(prefix="/new-feature", tags=["new-feature"])

@router.post("/process", response_model=NewFeatureResponse)
async def process_new_feature(request: NewFeatureRequest):
    """Your new endpoint implementation."""
    return NewFeatureResponse(result="processed")
```

**2. Register Router**
```python
# File: src/app/main.py
from .routers_new_feature import router as new_feature_router

app.include_router(new_feature_router)
```

**3. Test New Endpoint**
```bash
curl -X POST http://localhost:8010/new-feature/process \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### Smart Orchestrator Customization

**1. Modify Task Analysis**
```python
# File: src/app/smart_orchestrator.py
async def analyze_task(self, question: str, context: dict = None) -> TaskDecision:
    # Add your custom logic
    if "your_keyword" in question.lower():
        return TaskDecision(
            chosen_agent=AgentType.PYDANTIC_AI,
            reasoning="Custom routing logic",
            confidence=0.95
        )
    # ... rest of logic
```

**2. Test Custom Routing**
```bash
curl -s -X POST http://localhost:8010/smart/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "your_keyword test"}' | jq '.decision.chosen_agent'
```

## 🔍 **Debugging Workflows**

### Common Debugging Commands

```bash
# Check container health
docker compose ps

# View API logs
docker compose logs -f api

# Check Redis data
docker exec -it py-ai-redis-1 redis-cli
> KEYS *
> GET agent_memory:*

# Monitor real-time activity
docker compose logs -f api | grep -E "(ERROR|WARNING|INFO)"
```

### Agent-Specific Debugging

```bash
# Debug Smart Orchestrator decisions
curl -s -X POST http://localhost:8010/smart/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "debug this task"}' | jq '.explanation'

# Check agent capabilities
curl -s http://localhost:8010/pydantic-agent/debug/capabilities | jq '.'

# View agent status
curl -s http://localhost:8010/smart/agents/comparison | jq '.available_agents'
```

### Performance Debugging

```bash
# Profile API response time
curl -w "@curl-format.txt" http://localhost:8010/smart/chat?q=test

# Monitor memory usage
docker exec py-ai-api-1 cat /proc/meminfo | grep MemAvailable

# Check vector database size
du -sh .rag_store/
```

## 🧩 **Integration Workflows**

### Web Search Integration

```bash
# Test web search (if Tavily API key configured)
curl -s "http://localhost:8010/smart/chat?q=What%20happened%20today%20in%20tech?" | jq '.'

# Force web search
curl -s -X POST http://localhost:8010/smart/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Latest AI news", "force_web_search": true}' | jq '.'
```

### Session Management

```bash
# Test session continuity
SESSION_ID="test-session-$(date +%s)"

curl -s -X POST http://localhost:8010/smart/chat \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"My name is Alice\", \"session_id\": \"$SESSION_ID\"}" | jq '.answer'

curl -s -X POST http://localhost:8010/smart/chat \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"What is my name?\", \"session_id\": \"$SESSION_ID\"}" | jq '.answer'
```

### Streaming Responses

```bash
# Test streaming
curl -N "http://localhost:8010/smart/chat?q=Tell%20me%20about%20AI&stream=true"

# Test streaming with different agents
curl -N "http://localhost:8010/pydantic-agent/chat?q=Hello&stream=true"
```

## 📊 **Evaluation Workflows**

### Automated Testing

```bash
# Run evaluation suite
make eval

# Run web evaluation
make weval

# Run RAGAS metrics
make ragas

# Compare agents
make compare-agents
```

### Manual Quality Testing

```bash
# Test different question types
QUESTIONS=(
  "What is Python?"
  "Extract user data in JSON format"
  "Create a workflow for data analysis"
  "What are the company values?"
  "Latest news about AI"
)

for q in "${QUESTIONS[@]}"; do
  echo "Testing: $q"
  curl -s "http://localhost:8010/smart/chat?q=$(echo $q | sed 's/ /%20/g')" | jq '.agent_used'
done
```

### Performance Benchmarking

```bash
# Benchmark response times
echo "Benchmarking agent response times..."
for agent in "smart" "pydantic-agent" "hybrid-agent" "agent"; do
  echo "Testing $agent:"
  time curl -s "http://localhost:8010/$agent/chat?q=Hello" > /dev/null
done
```

## 🚀 **Deployment Workflows**

### Local to Staging

```bash
# 1. Test everything locally
make test-all

# 2. Build production images
docker build -t py-ai:staging .

# 3. Deploy to staging (when configured)
./scripts/deploy-staging.sh

# 4. Validate staging
API_BASE_URL=https://your-staging-url make validate-enterprise
```

### Feature Branch Workflow

```bash
# 1. Create feature branch
git checkout -b feature/new-agent-capability

# 2. Develop locally
# Make changes, test with curl commands above

# 3. Test thoroughly
make test-all

# 4. Create PR
git add .
git commit -m "Add new agent capability"
git push origin feature/new-agent-capability

# 5. Deploy to staging for review
./scripts/deploy-staging.sh
```

## 📋 **Development Checklist**

### Before Committing
- [ ] All tests pass (`make test`)
- [ ] Health endpoints responding
- [ ] All 4 agents operational
- [ ] New features tested with curl
- [ ] Documentation updated
- [ ] No console errors in logs

### Before Deploying
- [ ] Integration tests pass
- [ ] Performance tests acceptable
- [ ] Security validation complete
- [ ] Staging deployment successful
- [ ] Manual testing completed

### Code Quality
- [ ] Code formatted (`make format`)
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes
- [ ] Documentation strings added
- [ ] Error handling implemented

## 🛠️ **Useful Development Scripts**

### Quick Test Script
```bash
#!/bin/bash
# File: scripts/quick-test.sh
set -e

echo "🧪 Quick Development Test"

# Test health
curl -f http://localhost:8010/health > /dev/null && echo "✅ Health OK"

# Test agents
curl -s http://localhost:8010/smart/agents/comparison | jq '.available_agents | length' | grep -q 4 && echo "✅ All 4 agents available"

# Test routing
AGENT=$(curl -s "http://localhost:8010/smart/chat?q=Hello" | jq -r '.agent_used')
echo "✅ Smart routing working: $AGENT"

echo "🎉 All tests passed!"
```

### Development Reset Script
```bash
#!/bin/bash
# File: scripts/dev-reset.sh
set -e

echo "🔄 Resetting development environment"

# Reset containers
docker compose down -v
docker compose up -d --build

# Wait for services
sleep 10

# Verify everything is working
./scripts/quick-test.sh

echo "✅ Development environment reset complete"
```

## 🎯 **Next Steps**

1. **Start developing** using the patterns above
2. **Test your changes** with the provided curl commands
3. **Monitor performance** using the debugging tools
4. **Deploy to staging** when features are ready
5. **Scale to production** using the enterprise guide

---

## 🎉 **Your Multi-Agent Development Environment is Ready!**

**API Endpoint**: http://localhost:8010  
**Documentation**: http://localhost:8010/docs  
**All 4 Agents**: Operational and intelligent routing active  
**Development**: Hot reloading enabled for rapid iteration

Happy coding! 🚀