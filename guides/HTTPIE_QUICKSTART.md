# HTTPie Quick Start Guide

Fast setup and usage of HTTPie for py-ai platform testing.

## 🚀 Quick Setup (30 seconds)

```bash
# 1. HTTPie should already be installed
http --version  # Should show 3.2.4

# 2. Test basic connectivity
make py-test-httpie

# 3. Run development workflow
make py-dev-workflow
```

## 📋 **Available Make Commands**

```bash
# Development workflow
make py-dev-workflow     # Complete health check and testing
make py-test-httpie      # Basic HTTPie connectivity test
make py-aliases          # Show available aliases
make py-context7-demo    # Run Context7 integration demo
```

## 🛠️ **HTTPie Aliases Usage**

### Method 1: Source Aliases (Recommended)
```bash
# Source aliases in your shell
source scripts/httpie-aliases.sh

# Now use convenient commands
py-health                              # Health check
py-status                              # Smart orchestrator status  
py-chat q=="What is Python?"          # Chat with smart orchestrator
py-analyze-question "Your question"   # Analyze task routing
py-test-library "fastapi"             # Test library knowledge
```

### Method 2: Direct HTTPie Commands
```bash
# Basic health
http GET localhost:8010/health

# Smart orchestrator
http GET localhost:8010/smart/status
http GET localhost:8010/smart/agents/comparison

# Task analysis
echo '{"question": "Extract user data in JSON"}' | \
  http POST localhost:8010/smart/analyze

# Chat with different agents
http GET localhost:8010/smart/chat q=="What is Python?"
http GET localhost:8010/pydantic-agent/chat q=="Hello"
http GET localhost:8010/hybrid-agent/chat q=="Test"

# Document upload
http --form POST localhost:8010/docs/upload file@demo_docs/company_handbook.md
```

## 🧪 **Daily Testing Workflow**

### Morning Setup
```bash
# Start your dev environment
docker compose up -d

# Quick health check
make py-dev-workflow

# Or with aliases
source scripts/httpie-aliases.sh
py-dev-workflow
```

### During Development
```bash
# Test your changes
http GET localhost:8010/your-new-endpoint

# Test agent routing
py-analyze-question "Your development question"

# Test library knowledge  
py-test-library "your-library"

# Performance check
py-benchmark
```

### Before Commits
```bash
# Full test suite
make test

# Enterprise validation
make validate-enterprise

# HTTPie integration test
make py-test-httpie
```

## 🔍 **Troubleshooting**

### Common Issues

**1. Command not found: py-dev-workflow**
```bash
# Use Make command instead
make py-dev-workflow

# Or source aliases first
source scripts/httpie-aliases.sh
py-dev-workflow
```

**2. HTTPie not installed**
```bash
brew install httpie
```

**3. API not responding**
```bash
# Check Docker containers
docker compose ps

# Restart if needed
docker compose restart api
```

**4. Aliases not working**
```bash
# Make sure you sourced the file
source scripts/httpie-aliases.sh

# Add to your shell profile for permanent access
echo 'source ~/path/to/py-ai/scripts/httpie-aliases.sh' >> ~/.bashrc
# or ~/.zshrc for zsh
```

## 📊 **Testing Examples**

### Test All Agent Architectures
```bash
# Using aliases
source scripts/httpie-aliases.sh
py-chat q=="What is Python?"           # Smart orchestrator
py-pydantic q=="Hello"                 # Pydantic-AI  
py-hybrid q=="Test"                    # Hybrid agent
py-langgraph q=="Create workflow"      # LangGraph

# Using direct HTTPie
http GET localhost:8010/smart/agents/comparison
```

### Test Context7 Integration
```bash
# Library-specific questions
http GET localhost:8010/smart/chat \
  q=="How do I implement FastAPI dependency injection with type hints?"

# Multiple library testing
for lib in "fastapi" "pydantic" "sqlalchemy"; do
  echo "Testing $lib:"
  http GET localhost:8010/smart/chat q=="Best practices for $lib"
done
```

### Performance Testing
```bash
# Response times
time http GET localhost:8010/smart/status

# Concurrent requests
for i in {1..5}; do
  http GET localhost:8010/smart/status > /dev/null &
done
wait
```

## 🎯 **HTTPie vs curl Comparison**

| Task | curl | HTTPie |
|------|------|--------|
| GET request | `curl -X GET url` | `http GET url` |
| POST JSON | `curl -X POST -H "Content-Type: application/json" -d '{"key":"value"}' url` | `http POST url key=value` |
| Headers | `curl -H "Authorization: Bearer token" url` | `http url Authorization:"Bearer token"` |
| Pretty output | `curl url \| jq` | `http url` (automatic) |
| File upload | `curl -F "file=@path" url` | `http --form POST url file@path` |

## 📚 **Available Documentation**

- **Complete Guide**: `guides/HTTPIE_TESTING_GUIDE.md`
- **Local Development**: `guides/LOCAL_DEVELOPMENT_GUIDE.md`
- **Development Workflow**: `docs/DEVELOPMENT_WORKFLOW.md`
- **Aliases Reference**: `scripts/httpie-aliases.sh`

## 🎉 **Summary**

✅ **HTTPie installed and working**  
✅ **Make commands available** (`make py-dev-workflow`)  
✅ **Aliases ready** (`source scripts/httpie-aliases.sh`)  
✅ **All 4 agents tested and operational**  
✅ **Context7 integration demonstrated**  
✅ **Development workflow established**

**Quick Start**: `make py-dev-workflow`  
**Daily Use**: `source scripts/httpie-aliases.sh && py-help`

🚀 **Happy testing with HTTPie!**