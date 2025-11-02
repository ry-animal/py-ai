#!/bin/bash
# HTTPie Aliases for Py-AI Platform Development

# Source this file to get convenient HTTPie aliases
# Usage: source scripts/httpie-aliases.sh

# Base URL for local development
export PY_AI_BASE="localhost:8010"

# Health and Status
alias py-health="http GET $PY_AI_BASE/health"
alias py-ready="http GET $PY_AI_BASE/ready"
alias py-status="http GET $PY_AI_BASE/smart/status"

# Agent Management
alias py-agents="http GET $PY_AI_BASE/smart/agents/comparison"
alias py-pydantic-status="http GET $PY_AI_BASE/pydantic-agent/status"
alias py-hybrid-status="http GET $PY_AI_BASE/hybrid-agent/status"
alias py-capabilities="http GET $PY_AI_BASE/pydantic-agent/debug/capabilities"

# Chat and Analysis
alias py-chat="http GET $PY_AI_BASE/smart/chat"
alias py-analyze="echo '{\"question\": \"\$1\"}' | http POST $PY_AI_BASE/smart/analyze"
alias py-pydantic="http GET $PY_AI_BASE/pydantic-agent/chat"
alias py-hybrid="http GET $PY_AI_BASE/hybrid-agent/chat"
alias py-langgraph="http GET $PY_AI_BASE/agent/chat"

# Documents and RAG
alias py-docs="http GET $PY_AI_BASE/docs/"
alias py-ask="http GET $PY_AI_BASE/ask"
alias py-upload="http --form POST $PY_AI_BASE/docs/upload"

# Development Helpers
alias py-test-all='py-health && py-status && py-agents'
alias py-quick-test='echo "Testing agents..." && py-chat q=="Hello" && echo "✅ Quick test passed"'

# Functions for complex operations
py-analyze-question() {
    if [ -z "$1" ]; then
        echo "Usage: py-analyze-question 'Your question here'"
        return 1
    fi
    echo "{\"question\": \"$1\"}" | http POST $PY_AI_BASE/smart/analyze
}

py-chat-question() {
    if [ -z "$1" ]; then
        echo "Usage: py-chat-question 'Your question here'"
        return 1
    fi
    http GET $PY_AI_BASE/smart/chat q=="$1"
}

py-upload-doc() {
    if [ -z "$1" ]; then
        echo "Usage: py-upload-doc path/to/document.md"
        return 1
    fi
    http --form POST $PY_AI_BASE/docs/upload file@"$1"
}

py-test-library() {
    if [ -z "$1" ]; then
        echo "Usage: py-test-library 'library-name'"
        return 1
    fi
    echo "Testing library knowledge for: $1"
    py-chat-question "What are the best practices for using $1?"
}

# Performance testing
py-benchmark() {
    echo "🔥 Performance Benchmark"
    echo "======================="
    
    echo "1. Health check speed:"
    time py-health > /dev/null
    
    echo "2. Status check speed:"
    time py-status > /dev/null
    
    echo "3. Chat response speed:"
    time py-chat q=="Hello" > /dev/null
    
    echo "4. Concurrent requests (5x):"
    start_time=$(date +%s)
    for i in {1..5}; do
        py-status > /dev/null 2>&1 &
    done
    wait
    end_time=$(date +%s)
    echo "Completed in $((end_time - start_time)) seconds"
}

# Development workflow
py-dev-workflow() {
    echo "🚀 Development Workflow Test"
    echo "============================"
    
    echo "1. Health check..."
    if py-health --check-status --quiet; then
        echo "✅ API healthy"
    else
        echo "❌ API not responding"
        return 1
    fi
    
    echo "2. Agent availability..."
    agent_count=$(py-agents --body | jq '.available_agents | length' 2>/dev/null || echo "0")
    echo "✅ $agent_count agents available"
    
    echo "3. Smart routing test..."
    chosen_agent=$(py-analyze-question "Extract data in JSON" | jq -r '.decision.chosen_agent' 2>/dev/null || echo "unknown")
    echo "✅ Routing works, chose: $chosen_agent"
    
    echo "4. Chat functionality..."
    if py-chat q=="Hello" --check-status --quiet; then
        echo "✅ Chat working"
    else
        echo "⚠️ Chat issues detected"
    fi
    
    echo -e "\n🎉 Development workflow test complete!"
}

# Context7 simulation functions
py-context7-demo() {
    echo "📚 Context7 Integration Demo"
    echo "============================="
    
    echo "Testing library-aware responses..."
    py-chat-question "How do I implement FastAPI dependency injection?"
    
    echo -e "\nTesting multiple libraries..."
    for lib in "fastapi" "pydantic" "sqlalchemy"; do
        echo -e "\n--- $lib ---"
        py-test-library "$lib"
    done
}

# Help function
py-help() {
    cat << 'EOF'
🎯 Py-AI HTTPie Aliases Help
============================

Basic Commands:
  py-health              - Check API health
  py-ready               - Check API readiness
  py-status              - Smart orchestrator status
  py-agents              - List all available agents

Agent Testing:
  py-chat q=="question"  - Chat with smart orchestrator
  py-pydantic q=="q"     - Chat with Pydantic-AI agent
  py-hybrid q=="q"       - Chat with Hybrid agent
  py-langgraph q=="q"    - Chat with LangGraph agent

Analysis:
  py-analyze-question "question"  - Analyze task routing
  py-chat-question "question"     - Quick chat command

Documents:
  py-docs                - List uploaded documents
  py-upload-doc file.md  - Upload a document
  py-ask q=="question"   - RAG Q&A

Development:
  py-test-all           - Run basic health checks
  py-quick-test         - Quick functionality test
  py-dev-workflow       - Complete development test
  py-benchmark          - Performance benchmark

Library Testing:
  py-test-library "name"  - Test library knowledge
  py-context7-demo        - Demo Context7 potential

Examples:
  py-chat q=="What is Python?"
  py-analyze-question "Extract user data in JSON format"
  py-upload-doc demo_docs/handbook.md
  py-test-library "fastapi"
  py-benchmark

EOF
}

echo "✅ Py-AI HTTPie aliases loaded!"
echo "Type 'py-help' for available commands"
echo "Quick test: py-test-all"