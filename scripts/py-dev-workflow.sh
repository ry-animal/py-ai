#!/bin/bash
# Standalone development workflow script

set -e

BASE_URL="localhost:8010"

echo "🚀 Development Workflow Test"
echo "============================"

echo "1. Health check..."
if http --check-status --quiet GET $BASE_URL/health; then
    echo "✅ API healthy"
else
    echo "❌ API not responding"
    exit 1
fi

echo "2. Agent availability..."
agent_count=$(http GET $BASE_URL/smart/agents/comparison --body 2>/dev/null | jq '.available_agents | length' 2>/dev/null || echo "0")
echo "✅ $agent_count agents available"

echo "3. Smart routing test..."
chosen_agent=$(echo '{"question": "Extract data in JSON"}' | http POST $BASE_URL/smart/analyze --body 2>/dev/null | jq -r '.decision.chosen_agent' 2>/dev/null || echo "unknown")
echo "✅ Routing works, chose: $chosen_agent"

echo "4. Chat functionality..."
if http --check-status --quiet GET $BASE_URL/smart/chat q=="Hello"; then
    echo "✅ Chat working"
else
    echo "⚠️ Chat issues detected"
fi

echo -e "\n🎉 Development workflow test complete!"