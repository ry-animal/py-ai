# Enterprise Multi-Agent Platform - Manual Testing Guide

Complete manual testing procedures for validating the enterprise infrastructure and multi-agent system.

## 🎯 Pre-Testing Setup

### 1. Environment Preparation

```bash
# Install enterprise dependencies
uv sync --group enterprise

# Setup test environment
cp .env.enterprise.example .env.test
# Edit .env.test with test database configurations

# Start local services (if testing locally)
docker compose up -d redis  # For Redis
# Or use cloud services for full enterprise testing
```

### 2. Database Configuration Options

**Option A: Local Development Testing**
```bash
# .env.test configuration for local testing
VECTOR_DB_TYPE=chroma
MONGODB_URL=mongodb://localhost:27017/py_ai_test
POSTGRES_URL=postgresql://localhost:5432/py_ai_test
REDIS_URL=redis://localhost:6379/0
```

**Option B: Enterprise Cloud Testing**
```bash
# .env.test configuration for cloud services
VECTOR_DB_TYPE=vertex  # or snowflake, cockroach
GCP_PROJECT_ID=your-test-project
MONGODB_URL=mongodb+srv://test-cluster/py_ai_staging
POSTGRES_URL=postgresql://test-host:5432/py_ai_staging
REDIS_URL=redis://test-redis:6379/0
```

## 🧪 Manual Testing Procedures

### 1. Infrastructure Validation

#### 1.1 Database Adapter Testing

```bash
# Test MongoDB adapter
make test-mongodb

# Test PostgreSQL adapter  
make test-postgres

# Test vector database adapter
make test-vector-db

# Test all databases together
make test-databases
```

**Expected Output:**
- ✅ Successful connection to each database
- ✅ Proper error handling if databases unavailable
- ✅ Adapter initialization without errors

#### 1.2 Enterprise Configuration Testing

```bash
# Validate enterprise configuration loading
uv run python -c "
from src.app.config import get_settings
settings = get_settings()
print(f'Vector DB: {settings.vector_db_type}')
print(f'MongoDB: {\"✅\" if settings.mongodb_url else \"❌\"}')
print(f'PostgreSQL: {\"✅\" if settings.postgres_url else \"❌\"}')
print(f'Multi-Agent: {settings.enable_smart_orchestrator}')
"
```

### 2. Multi-Agent System Testing

#### 2.1 Start the Enterprise API

```bash
# Start with enterprise configuration
ENV_FILE=.env.test make run

# Or with Docker for full enterprise stack
docker compose up --build
```

#### 2.2 Health Check Validation

```bash
# Basic health checks
curl -s http://localhost:8000/health | jq '.'
curl -s http://localhost:8000/ready | jq '.'

# Expected: {"status": "healthy"} with system information
```

#### 2.3 Smart Orchestrator Testing

**Test 1: Status and Capabilities**
```bash
# Check smart orchestrator status
curl -s http://localhost:8000/smart/status | jq '.'

# Expected output:
{
  "status": "ready",
  "architecture": "Smart Multi-Agent Orchestrator",
  "available_agents": ["langgraph", "pydantic_ai", "hybrid"],
  "selection_logic": { ... },
  "features": [ ... ]
}
```

**Test 2: Task Analysis**
```bash
# Test structured output task analysis
curl -s -X POST http://localhost:8000/smart/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "Extract user data in JSON format"}' | jq '.'

# Expected: chosen_agent = "pydantic_ai", confidence >= 85%

# Test complex workflow task analysis
curl -s -X POST http://localhost:8000/smart/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "Analyze ML models and create improvement workflow"}' | jq '.'

# Expected: chosen_agent = "langgraph", task_category = "workflow"
```

**Test 3: Agent Comparison**
```bash
# Get agent comparison matrix
curl -s http://localhost:8000/smart/agents/comparison | jq '.available_agents | keys'

# Expected: ["langgraph", "pydantic_ai", "hybrid", "smart_orchestrator"]
```

#### 2.4 Individual Agent Testing

**Test 1: Pydantic-AI Agent**
```bash
# Check status
curl -s http://localhost:8000/pydantic-agent/status | jq '.'

# Test chat functionality
curl -s "http://localhost:8000/pydantic-agent/chat?q=What%20is%20Python?" | jq '.answer'

# Test AG-UI endpoint
curl -s http://localhost:8000/pydantic-agent/ag-ui | jq '.'

# Test capabilities
curl -s http://localhost:8000/pydantic-agent/debug/capabilities | jq '.tools'
```

**Test 2: Hybrid Agent**
```bash
# Check status
curl -s http://localhost:8000/hybrid-agent/status | jq '.'

# Test chat functionality
curl -s "http://localhost:8000/hybrid-agent/chat?q=Hello%20world" | jq '.answer'

# Check architecture details
curl -s http://localhost:8000/hybrid-agent/architecture | jq '.'
```

**Test 3: LangGraph Agent**
```bash
# Test original agent
curl -s "http://localhost:8000/agent/chat?q=What%20is%20FastAPI?" | jq '.answer'
```

#### 2.5 Smart Orchestrator Intelligence Testing

**Test Scenario 1: Simple Q&A (should route to Pydantic-AI)**
```bash
curl -s "http://localhost:8000/smart/chat?q=What%20is%20Python?" | jq '{
  answer: .answer,
  agent_used: .agent_used,
  orchestration: .orchestration.chosen_agent
}'

# Expected: agent_used = "pydantic_ai"
```

**Test Scenario 2: Structured Output (should route to Pydantic-AI)**
```bash
curl -s -X POST http://localhost:8000/smart/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Extract user information in JSON format"}' | jq '{
  agent_used: .agent_used,
  confidence: .orchestration.confidence
}'

# Expected: agent_used = "pydantic_ai", confidence >= 90%
```

**Test Scenario 3: Complex Workflow (should route to LangGraph)**
```bash
curl -s -X POST http://localhost:8000/smart/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Create a multi-step analysis workflow for our data"}' | jq '{
  agent_used: .agent_used,
  task_complexity: .orchestration.task_complexity
}'

# Expected: agent_used = "langgraph", task_complexity = "complex"
```

**Test Scenario 4: Force Agent Selection**
```bash
# Force Pydantic-AI agent
curl -s -X POST http://localhost:8000/smart/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello", "force_agent": "pydantic_ai"}' | jq '.agent_used'

# Expected: "pydantic_ai"
```

### 3. Performance Testing

#### 3.1 Concurrent Request Testing

```bash
# Test concurrent requests to smart orchestrator
for i in {1..10}; do
  curl -s "http://localhost:8000/smart/status" &
done
wait

echo "All concurrent requests completed"
```

#### 3.2 Response Time Testing

```bash
# Measure response times
time curl -s "http://localhost:8000/smart/chat?q=Hello" > /dev/null
time curl -s "http://localhost:8000/pydantic-agent/chat?q=Hello" > /dev/null
time curl -s "http://localhost:8000/hybrid-agent/chat?q=Hello" > /dev/null

# Expected: All responses < 2 seconds
```

#### 3.3 Memory Usage Testing

```bash
# Monitor memory during load testing
./scripts/load_test.sh &  # If available
top -p $(pgrep -f uvicorn)
```

### 4. Streaming Support Testing

```bash
# Test streaming responses
curl -N "http://localhost:8000/smart/chat?q=Tell%20me%20about%20AI&stream=true"

# Expected: Server-sent events stream
```

### 5. Error Handling Testing

#### 5.1 Invalid Input Testing

```bash
# Test malformed JSON
curl -s -X POST http://localhost:8000/smart/analyze \
  -H "Content-Type: application/json" \
  -d 'invalid json'

# Expected: 422 validation error

# Test missing required fields
curl -s -X POST http://localhost:8000/smart/analyze \
  -H "Content-Type: application/json" \
  -d '{}'

# Expected: 422 validation error
```

#### 5.2 Non-existent Endpoint Testing

```bash
# Test 404 handling
curl -s http://localhost:8000/nonexistent/endpoint

# Expected: 404 Not Found
```

### 6. Database Integration Testing

#### 6.1 MongoDB Document Storage (if configured)

```bash
# Test document storage functionality
curl -s -X POST http://localhost:8000/docs/upload \
  -F "file=@README.md"

# Test document listing
curl -s http://localhost:8000/docs/ | jq '.'
```

#### 6.2 PostgreSQL Session Management (if configured)

```bash
# Test session creation and tracking
curl -s -X POST http://localhost:8000/smart/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello", "session_id": "test-session-123"}' | jq '.session_id'
```

### 7. Enterprise Feature Testing

#### 7.1 Multi-Agent Make Commands

```bash
# Test all agent architectures
make test-all-agents

# Get agent status summary
make agent-status

# Run integration demo
make demo-integration

# Validate enterprise deployment
API_BASE_URL=http://localhost:8000 make validate-enterprise
```

#### 7.2 Configuration Switching

```bash
# Test different vector database configurations
export VECTOR_DB_TYPE=vertex
make test-vector-db

export VECTOR_DB_TYPE=cockroach
make test-vector-db

export VECTOR_DB_TYPE=chroma
make test-vector-db
```

## 🔍 Validation Checklist

### ✅ Infrastructure Tests
- [ ] All database adapters initialize without errors
- [ ] Enterprise configuration loads correctly
- [ ] Health endpoints respond successfully
- [ ] Error handling works for missing databases

### ✅ Multi-Agent System Tests
- [ ] Smart orchestrator status shows all 4 agents
- [ ] Task analysis correctly categorizes different question types
- [ ] Agent comparison endpoint lists all architectures
- [ ] All individual agent endpoints respond

### ✅ Intelligence Tests
- [ ] Simple Q&A routes to Pydantic-AI
- [ ] Structured output tasks route to Pydantic-AI with high confidence
- [ ] Complex workflows route to LangGraph
- [ ] Agent forcing works correctly
- [ ] Fallback mechanisms trigger on errors

### ✅ Performance Tests
- [ ] Concurrent requests handle properly
- [ ] Response times are reasonable (< 2 seconds)
- [ ] Memory usage remains stable
- [ ] No memory leaks during extended testing

### ✅ Feature Tests
- [ ] Streaming responses work where implemented
- [ ] Input validation catches malformed requests
- [ ] CORS headers present
- [ ] Request ID tracking functional

### ✅ Enterprise Integration Tests
- [ ] Make commands execute successfully
- [ ] Database configuration switching works
- [ ] Document upload/management functional (if databases configured)
- [ ] Session management working (if databases configured)

## 🚨 Common Issues and Troubleshooting

### Issue 1: Database Connection Failures
**Symptoms**: Adapter tests fail with connection errors
**Solution**: Check database URLs, ensure services are running, verify network connectivity

### Issue 2: Agent Selection Not Working
**Symptoms**: Smart orchestrator always picks same agent
**Solution**: Check task analysis logic, verify all agents are initialized

### Issue 3: Import Errors
**Symptoms**: Module import failures
**Solution**: Ensure `uv sync --group enterprise` was run, check Python path

### Issue 4: Performance Issues
**Symptoms**: Slow response times, high memory usage
**Solution**: Check for blocking operations, verify async/await usage, monitor database performance

### Issue 5: Streaming Not Working
**Symptoms**: Streaming endpoints return regular JSON
**Solution**: Verify streaming implementation, check client support for Server-Sent Events

## 📊 Performance Benchmarks

**Expected Response Times:**
- Health endpoints: < 100ms
- Status endpoints: < 200ms
- Task analysis: < 500ms
- Simple chat requests: < 2 seconds
- Complex workflow requests: < 5 seconds

**Expected Memory Usage:**
- Base application: < 200MB
- Under load (100 requests): < 300MB
- Memory increase per hour: < 50MB

**Expected Throughput:**
- Status endpoints: > 100 req/sec
- Chat endpoints: > 10 req/sec
- Concurrent connections: > 50

## 📋 Test Report Template

```markdown
# Enterprise Testing Report

**Date**: [DATE]
**Environment**: [local/staging/production]
**Tester**: [NAME]

## Infrastructure Tests
- [ ] Database adapters: PASS/FAIL
- [ ] Configuration loading: PASS/FAIL
- [ ] Health checks: PASS/FAIL

## Multi-Agent Tests  
- [ ] Smart orchestrator: PASS/FAIL
- [ ] Agent selection: PASS/FAIL
- [ ] All endpoints: PASS/FAIL

## Performance Tests
- [ ] Response times: PASS/FAIL
- [ ] Concurrent requests: PASS/FAIL
- [ ] Memory usage: PASS/FAIL

## Issues Found
1. [Issue description]
2. [Issue description]

## Overall Assessment
- Ready for deployment: YES/NO
- Critical issues: [COUNT]
- Recommendations: [LIST]
```

---

**🎯 Testing complete!** This manual testing guide ensures comprehensive validation of all enterprise features before production deployment.