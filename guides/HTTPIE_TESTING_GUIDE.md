# HTTPie Testing Guide for Py-AI Platform

User-friendly API testing with HTTPie for the multi-agent platform.

## 🎯 HTTPie vs curl - Why HTTPie is Better

HTTPie provides:
- **Human-friendly syntax**: `http GET url` vs `curl -X GET url`
- **Pretty JSON output**: Automatic formatting and colors
- **Easy headers**: `header:value` vs `-H "header: value"`
- **Request/Response inspection**: Shows both by default
- **Session support**: Save authentication and cookies

## 🚀 Quick Start

### Basic HTTPie Syntax
```bash
# GET request
http GET localhost:8010/health

# POST request with JSON data
http POST localhost:8010/smart/analyze question="What is Python?"

# GET with query parameters
http GET localhost:8010/smart/chat q=="Hello World"

# Custom headers
http GET localhost:8010/smart/status Authorization:"Bearer token"
```

## 🧪 Testing All Agent Architectures

### 1. Health & Status Checks

```bash
# Basic health check
http GET localhost:8010/health

# Readiness check
http GET localhost:8010/ready

# Smart orchestrator status
http GET localhost:8010/smart/status

# All agents comparison
http GET localhost:8010/smart/agents/comparison
```

### 2. Smart Orchestrator Testing

```bash
# Test intelligent task analysis
http POST localhost:8010/smart/analyze \
  question="Extract user data in JSON format"

# Test complex workflow routing
http POST localhost:8010/smart/analyze \
  question="Create a comprehensive data analysis workflow with multiple steps"

# Test simple Q&A routing
http GET localhost:8010/smart/chat q=="What is Python?"

# Force specific agent
http POST localhost:8010/smart/chat \
  question="Hello" \
  force_agent="pydantic_ai"

# With session ID
http POST localhost:8010/smart/chat \
  question="My name is Alice" \
  session_id="test-session-123"

# Continue conversation
http POST localhost:8010/smart/chat \
  question="What is my name?" \
  session_id="test-session-123"
```

### 3. Individual Agent Testing

```bash
# Pydantic-AI Agent
http GET localhost:8010/pydantic-agent/status
http GET localhost:8010/pydantic-agent/chat q=="Hello"
http GET localhost:8010/pydantic-agent/debug/capabilities
http GET localhost:8010/pydantic-agent/ag-ui

# Hybrid Agent
http GET localhost:8010/hybrid-agent/status
http GET localhost:8010/hybrid-agent/chat q=="Test hybrid functionality"
http GET localhost:8010/hybrid-agent/architecture

# LangGraph Agent
http GET localhost:8010/agent/chat q=="Create a workflow"

# All agent status check
for agent in "smart" "pydantic-agent" "hybrid-agent" "agent"; do
  echo "=== $agent Status ==="
  http GET localhost:8010/$agent/status 2>/dev/null || echo "No status endpoint"
done
```

## 📄 Document Management & RAG

### Document Upload

```bash
# Upload a document (using form data)
http --form POST localhost:8010/docs/upload \
  file@demo_docs/company_handbook.md

# List uploaded documents
http GET localhost:8010/docs/

# Get specific document
http GET localhost:8010/docs/your-doc-id
```

### RAG Testing

```bash
# Manual RAG reload
http POST localhost:8010/rag/reload \
  Content-Type:application/json \
  <<< '[["1","Our company values include innovation, collaboration, and customer focus."]]'

# Test RAG Q&A
http GET localhost:8010/ask q=="What are the company values?"

# Enhanced chat with citations
http POST localhost:8010/chat/ \
  message="What are the company core values?"

# Stream chat response
http --stream GET localhost:8010/chat/stream q=="Tell me about the company"

# Get conversation history
http GET localhost:8010/chat/sessions/test-session-123/history

# Clear session
http DELETE localhost:8010/chat/sessions/test-session-123
```

## 🔍 MCP Context7 Integration Testing

Since you have MCP Context7 available, let's test library documentation retrieval:

### Test Context7 Library Resolution

```bash
# Test if Context7 is working (this would be internal to your system)
# But we can test endpoints that might use Context7 data

# Test if the platform has library documentation features
http GET localhost:8010/docs/libraries  # If implemented

# Test API documentation endpoints
http GET localhost:8010/docs  # OpenAPI/Swagger docs

# Test if there are any library-specific endpoints
http GET localhost:8010/debug/mcp  # If implemented

# Check for any Context7 integration status
http GET localhost:8010/system/mcp/status  # If implemented
```

### Creating Context7-Enhanced Endpoints

If you want to add Context7 integration, here's how you might test it:

```bash
# Hypothetical Context7-enhanced endpoints
http POST localhost:8010/library/docs \
  library="fastapi" \
  topic="routing"

http POST localhost:8010/library/search \
  query="async database connections" \
  library="sqlalchemy"

# Test library-aware code generation
http POST localhost:8010/smart/chat \
  question="How do I create FastAPI routes with dependency injection?" \
  context="library:fastapi"
```

## 🔧 Advanced Testing Scenarios

### Performance Testing

```bash
# Response time measurement
time http GET localhost:8010/smart/status

# Concurrent requests (background jobs)
for i in {1..5}; do
  http GET localhost:8010/smart/status > /dev/null 2>&1 &
done
wait
echo "All concurrent requests completed"

# Large request testing
http POST localhost:8010/smart/analyze \
  question="$(cat demo_docs/company_handbook.md)"
```

### Streaming Support

```bash
# Test streaming responses
http --stream GET localhost:8010/smart/chat \
  q=="Tell me a long story about AI" \
  stream==true

# Stream with different agents
http --stream GET localhost:8010/pydantic-agent/chat \
  q=="Explain machine learning concepts" \
  stream==true
```

### Error Handling Testing

```bash
# Test malformed JSON
echo "invalid json" | http POST localhost:8010/smart/analyze \
  Content-Type:application/json

# Test missing parameters
http POST localhost:8010/smart/analyze

# Test invalid endpoints
http GET localhost:8010/nonexistent/endpoint

# Test rate limiting (if implemented)
for i in {1..200}; do
  http GET localhost:8010/smart/status > /dev/null 2>&1
done
```

## 🛠️ HTTPie Productivity Tips

### Sessions for Authentication

```bash
# Create a session (if your API uses auth)
http --session=py-ai POST localhost:8010/auth/login \
  username=test password=test

# Use session for subsequent requests
http --session=py-ai GET localhost:8010/smart/status
```

### Pretty Output and Filtering

```bash
# Pretty print JSON
http GET localhost:8010/smart/agents/comparison | jq '.'

# Filter specific fields
http GET localhost:8010/smart/status | jq '.available_agents'

# Save response to file
http GET localhost:8010/smart/agents/comparison > agents_comparison.json

# Show only response body
http --body GET localhost:8010/smart/status

# Show only headers
http --headers GET localhost:8010/smart/status
```

### HTTPie Configuration

```bash
# Create HTTPie config directory
mkdir -p ~/.config/httpie

# Create config file
cat > ~/.config/httpie/config.json << 'EOF'
{
    "default_options": [
        "--print=HhBb",
        "--style=monokai",
        "--timeout=30"
    ]
}
EOF
```

## 📊 HTTPie Testing Scripts

### Comprehensive Test Script

```bash
#!/bin/bash
# File: scripts/httpie-test-all.sh

echo "🧪 HTTPie Comprehensive Test Suite"
echo "=================================="

BASE_URL="localhost:8010"

# Health checks
echo "1. Health Checks"
http GET $BASE_URL/health --check-status
http GET $BASE_URL/ready --check-status

# Agent availability
echo -e "\n2. Agent Availability"
AGENTS=$(http GET $BASE_URL/smart/agents/comparison --body | jq -r '.available_agents | keys[]')
echo "Available agents: $AGENTS"

# Smart orchestrator
echo -e "\n3. Smart Orchestrator Intelligence"
http POST $BASE_URL/smart/analyze \
  question="Extract user data in JSON format" \
  --body | jq '.decision'

# Individual agents
echo -e "\n4. Individual Agent Tests"
http GET $BASE_URL/smart/chat q=="Hello" --body | jq '.agent_used'
http GET $BASE_URL/pydantic-agent/chat q=="Hi" --body | jq '.answer'

# RAG functionality
echo -e "\n5. RAG System Test"
http POST $BASE_URL/rag/reload \
  <<< '[["test","Company values include innovation and collaboration"]]' \
  --body

sleep 2
http GET $BASE_URL/ask q=="What are the company values?" --body | jq '.answer'

echo -e "\n✅ All tests completed!"
```

### Performance Benchmark Script

```bash
#!/bin/bash
# File: scripts/httpie-benchmark.sh

echo "⚡ HTTPie Performance Benchmark"
echo "=============================="

BASE_URL="localhost:8010"

# Response time test
echo "1. Response Time Tests"
for endpoint in "health" "ready" "smart/status"; do
  echo "Testing /$endpoint:"
  time http GET $BASE_URL/$endpoint --body > /dev/null
done

# Concurrent requests
echo -e "\n2. Concurrent Request Test"
start_time=$(date +%s)
for i in {1..10}; do
  http GET $BASE_URL/smart/status --body > /dev/null 2>&1 &
done
wait
end_time=$(date +%s)
echo "10 concurrent requests completed in $((end_time - start_time)) seconds"

# Agent routing performance
echo -e "\n3. Agent Routing Performance"
time http POST $BASE_URL/smart/analyze \
  question="Test routing performance" \
  --body > /dev/null

echo -e "\n📊 Benchmark completed!"
```

### Development Testing Script

```bash
#!/bin/bash
# File: scripts/httpie-dev-test.sh

echo "🔧 HTTPie Development Testing"
echo "============================="

BASE_URL="localhost:8010"

# Quick development checks
echo "1. Quick Health Check"
if http GET $BASE_URL/health --check-status --quiet; then
  echo "✅ API is healthy"
else
  echo "❌ API is not responding"
  exit 1
fi

# Test your latest changes
echo -e "\n2. Testing Latest Changes"
echo "Add your specific test cases here..."

# Test new endpoints (example)
# http GET $BASE_URL/your-new-endpoint

# Test modified agent behavior
http POST $BASE_URL/smart/analyze \
  question="Test your latest feature" \
  --body | jq '.decision.chosen_agent'

echo -e "\n✅ Development tests completed!"
```

## 🎯 **Quick Reference Commands**

```bash
# Essential HTTPie commands for daily development
alias py-health="http GET localhost:8010/health"
alias py-status="http GET localhost:8010/smart/status"
alias py-agents="http GET localhost:8010/smart/agents/comparison"
alias py-chat="http GET localhost:8010/smart/chat"
alias py-analyze="http POST localhost:8010/smart/analyze"

# Usage examples:
py-health
py-chat q=="What is Python?"
py-analyze question="Extract data in JSON"
```

## 📚 **HTTPie Resources**

- **HTTPie Documentation**: https://httpie.io/docs
- **HTTPie CLI Reference**: `http --help`
- **JSON Processing**: Use with `jq` for powerful filtering
- **Scripting**: Great for automation and CI/CD testing

---

🎉 **HTTPie is now ready for testing your multi-agent platform!**

Try the commands above to explore your platform's capabilities with a much better developer experience than curl.