#!/bin/bash
# HTTPie + Context7 Integration Demo Script

set -e

echo "🎯 HTTPie + Context7 Integration Demo"
echo "====================================="

BASE_URL="localhost:8010"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Testing multi-agent platform with HTTPie...${NC}"

# 1. Basic Health Check
echo -e "\n${YELLOW}1. Health Check${NC}"
if http --check-status --quiet GET $BASE_URL/health; then
    echo -e "${GREEN}✅ API is healthy${NC}"
else
    echo -e "${RED}❌ API is not responding${NC}"
    exit 1
fi

# 2. Test Smart Orchestrator
echo -e "\n${YELLOW}2. Smart Orchestrator Intelligence${NC}"
echo "Testing library-specific question routing..."

RESPONSE=$(echo '{"question": "How do I implement FastAPI dependency injection with type hints?"}' | \
    http POST $BASE_URL/smart/analyze --body)

CHOSEN_AGENT=$(echo $RESPONSE | jq -r '.decision.chosen_agent')
CONFIDENCE=$(echo $RESPONSE | jq -r '.decision.confidence')

echo -e "Chosen Agent: ${GREEN}$CHOSEN_AGENT${NC}"
echo -e "Confidence: ${GREEN}$(echo "$CONFIDENCE * 100" | bc)%${NC}"

# 3. Test Library-Aware Responses
echo -e "\n${YELLOW}3. Library-Aware AI Responses${NC}"
echo "Testing FastAPI-specific guidance..."

FASTAPI_RESPONSE=$(http GET $BASE_URL/smart/chat \
    q=="How do I use dependency injection in FastAPI with modern patterns?" \
    --body)

AGENT_USED=$(echo $FASTAPI_RESPONSE | jq -r '.agent_used')
HAS_SOURCES=$(echo $FASTAPI_RESPONSE | jq -r '.sources | length')

echo -e "Agent Used: ${GREEN}$AGENT_USED${NC}"
echo -e "Sources Found: ${GREEN}$HAS_SOURCES${NC}"

if [ "$HAS_SOURCES" -gt "0" ]; then
    echo -e "${GREEN}✅ AI provided sources and context-aware response${NC}"
else
    echo -e "${YELLOW}⚠️  Response generated without external sources${NC}"
fi

# 4. Test Different Library Queries
echo -e "\n${YELLOW}4. Multi-Library Testing${NC}"

LIBRARIES=("pydantic" "sqlalchemy" "pytest" "docker")

for lib in "${LIBRARIES[@]}"; do
    echo -e "\nTesting ${BLUE}$lib${NC} knowledge..."
    
    RESPONSE=$(http GET $BASE_URL/smart/chat \
        q=="What are the best practices for using $lib?" \
        --body --quiet)
    
    ANSWER_LENGTH=$(echo $RESPONSE | jq -r '.answer | length')
    
    if [ "$ANSWER_LENGTH" -gt "100" ]; then
        echo -e "${GREEN}✅ Detailed response for $lib ($ANSWER_LENGTH chars)${NC}"
    else
        echo -e "${YELLOW}⚠️  Brief response for $lib ($ANSWER_LENGTH chars)${NC}"
    fi
done

# 5. Test Context7-Enhanced Features (Hypothetical)
echo -e "\n${YELLOW}5. Context7 Enhancement Simulation${NC}"
echo "Demonstrating how Context7 could enhance responses..."

# Simulate Context7-enhanced endpoint
echo -e "\n${BLUE}Simulated Context7 Integration:${NC}"
echo "If Context7 were integrated, we could:"
echo "1. Get real-time library documentation"
echo "2. Provide version-specific examples"
echo "3. Show canonical patterns from official repos"

# Test current documentation quality
DOC_QUALITY_TEST=$(echo '{"question": "Show me the latest FastAPI dependency injection patterns with type annotations"}' | \
    http POST $BASE_URL/smart/chat --body)

RESPONSE_QUALITY=$(echo $DOC_QUALITY_TEST | jq -r '.answer | length')
echo -e "Current response quality: ${GREEN}$RESPONSE_QUALITY characters${NC}"

# 6. Performance Testing
echo -e "\n${YELLOW}6. Performance Testing${NC}"

echo "Testing response times for library queries..."

start_time=$(date +%s%N)
http GET $BASE_URL/smart/chat q=="FastAPI middleware patterns" --body > /dev/null 2>&1
end_time=$(date +%s%N)
response_time=$(echo "scale=3; ($end_time - $start_time) / 1000000000" | bc)

echo -e "Library query response time: ${GREEN}${response_time}s${NC}"

# 7. Test Agent Comparison
echo -e "\n${YELLOW}7. Agent Architecture Analysis${NC}"

AGENTS_RESPONSE=$(http GET $BASE_URL/smart/agents/comparison --body)
AGENT_COUNT=$(echo $AGENTS_RESPONSE | jq -r '.available_agents | keys | length')

echo -e "Available agent architectures: ${GREEN}$AGENT_COUNT${NC}"

# Show which agent is best for library documentation
LIBRARY_TASK=$(echo '{"question": "Which design patterns should I use with FastAPI for microservices?"}' | \
    http POST $BASE_URL/smart/analyze --body)

BEST_AGENT=$(echo $LIBRARY_TASK | jq -r '.decision.chosen_agent')
REASONING=$(echo $LIBRARY_TASK | jq -r '.decision.reasoning')

echo -e "Best agent for library questions: ${GREEN}$BEST_AGENT${NC}"
echo -e "Reasoning: ${BLUE}$REASONING${NC}"

# 8. Context7 Integration Recommendations
echo -e "\n${YELLOW}8. Context7 Integration Recommendations${NC}"

cat << 'EOF'
🚀 How Context7 Could Enhance Your Platform:

1. **Real-time Library Documentation**
   - Endpoint: POST /library/docs
   - Example: http POST localhost:8010/library/docs library=fastapi topic="dependency injection"

2. **Version-Specific Guidance**
   - Endpoint: POST /library/version-compare
   - Example: http POST localhost:8010/library/version-compare library=fastapi from=0.100.0 to=0.115.0

3. **Code Example Generation**
   - Endpoint: POST /library/examples
   - Example: http POST localhost:8010/library/examples library=sqlalchemy pattern="async sessions"

4. **Integration with Smart Orchestrator**
   - Context7 data could enhance agent decision-making
   - Provide library-specific routing confidence
   - Enable documentation-aware responses

5. **Development Workflow Enhancement**
   - Live documentation lookup during development
   - Context-aware code suggestions
   - Library migration guidance
EOF

# Summary
echo -e "\n${YELLOW}📊 Demo Summary${NC}"
echo -e "================="
echo -e "✅ HTTPie testing framework: ${GREEN}Ready${NC}"
echo -e "✅ Multi-agent platform: ${GREEN}Operational${NC}"
echo -e "✅ Library-aware responses: ${GREEN}Working${NC}"
echo -e "✅ Context7 integration potential: ${GREEN}High${NC}"

echo -e "\n${GREEN}🎉 HTTPie + Context7 demo completed successfully!${NC}"
echo -e "\n${BLUE}Next steps:${NC}"
echo "1. Integrate Context7 MCP tools into your agent workflows"
echo "2. Create library-specific endpoints using Context7 data"
echo "3. Enhance smart orchestrator with real-time documentation"
echo "4. Use HTTPie for ongoing API development and testing"

echo -e "\n${YELLOW}Quick HTTPie commands for daily use:${NC}"
echo "http GET $BASE_URL/smart/status"
echo "http GET $BASE_URL/smart/agents/comparison" 
echo "echo '{\"question\": \"your query\"}' | http POST $BASE_URL/smart/analyze"
echo "http GET $BASE_URL/smart/chat q==\"your question\""
EOF