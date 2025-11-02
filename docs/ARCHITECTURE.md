# Enterprise Multi-Agent AI Platform Architecture

## System Overview

The AI Platform is an enterprise-ready, multi-agent AI system with production CI/CD, multi-cloud database support, and intelligent orchestration. It provides four distinct agent architectures, enterprise-grade infrastructure, and comprehensive monitoring. The system integrates with Harness CI/CD, Terraform infrastructure management, and supports multiple vector database providers including Vertex AI, Snowflake Cortex, and CockroachDB.

## Enterprise Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT INTERFACES                           │
├─────────────────────────────────────────────────────────────────┤
│  • HTTP API (FastAPI)                                           │
│  • OpenUI Frontend Integration                                  │
│  • AG-UI Protocol Support                                       │
│  • Interactive Documentation (/docs)                            │
│  • Streaming & Non-streaming Chat                               │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│                  ENTERPRISE API GATEWAY                         │
├─────────────────────────────────────────────────────────────────┤
│  • Load Balancer (Cloud Run / K8s Ingress)                      │
│  • CORS Middleware                                              │
│  • Rate Limiting (120-200 req/min per client)                   │
│  • Request Size Limits (2-10MB configurable)                    │
│  • Request ID Tracking & Logging                                │
│  • OpenTelemetry Instrumentation                                │
│  • Security Scanning & WAF                                      │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│                   ROUTING LAYER                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐     │
│  │   /docs/*   │    │   /chat/*    │    │   /tasks/*      │     │
│  │             │    │              │    │                 │     │
│  │ • Upload    │    │ • Chat       │    │ • Job Status    │     │
│  │ • List      │    │ • Stream     │    │ • Progress      │     │
│  │ • Delete    │    │ • History    │    │ • Results       │     │
│  │ • Status    │    │ • Sessions   │    │                 │     │
│  └─────────────┘    └──────────────┘    └─────────────────┘     │
│                                                                 │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│                  BUSINESS LOGIC LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ DocumentService │  │  AgentService    │  │   AIService     │ │
│  │                 │  │                  │  │                 │ │
│  │ • File Upload   │  │ • Route Decision │  │ • OpenAI        │ │
│  │ • Text Extract  │  │ • Context Merge  │  │ • Anthropic     │ │
│  │ • Validation    │  │ • Citation Gen   │  │ • Fallback      │ │
│  │ • Metadata      │  │ • Session Mgmt   │  │ • Streaming     │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                 │
└─────────┬───────────────────────┬───────────────────────────────┘
          │                       │
          ▼                       ▼
┌─────────────────┐     ┌─────────────────────────────────────────┐
│ MULTI-AGENT     │     │        ENTERPRISE DATA LAYER            │
│ CORE SYSTEM     │     ├─────────────────────────────────────────┤
├─────────────────┤     │                                         │
│                 │     │  ┌─────────────┐  ┌─────────────────┐   │
│ ┌─────────────┐ │     │  │ MongoDB     │  │ Multi-Cloud     │   │
│ │Smart Orch.  │ │     │  │ Adapter     │  │ Vector Store    │   │
│ │             │ │     │  │             │  │                 │   │
│ │ ┌─────────┐ │ │     │  │ • Documents │  │ • Vertex AI     │   │
│ │ │LangGraph│ │ │     │  │ • Full-text │  │ • Snowflake     │   │
│ │ │ Agent   │ │ │◄────┤  │ • Metadata  │  │ • CockroachDB   │   │
│ │ └─────────┘ │ │     │  └─────────────┘  │ • ChromaDB      │   │
│ │ ┌─────────┐ │ │     │                   └─────────────────┘   │
│ │ │Pydantic │ │ │     │  ┌─────────────┐  ┌─────────────────┐   │
│ │ │AI Agent │ │ │     │  │ PostgreSQL  │  │     Redis       │   │
│ │ └─────────┘ │ │     │  │ Adapter     │  │   Cluster       │   │
│ │ ┌─────────┐ │ │     │  │             │  │                 │   │
│ │ │ Hybrid  │ │ │     │  │ • Sessions  │  │ • Cache Layer   │   │
│ │ │ Agent   │ │ │     │  │ • Metrics   │  │ • Celery Queue  │   │
│ │ └─────────┘ │ │     │  │ • Audit Log │  │ • Session TTL   │   │
│ └─────────────┘ │     │  └─────────────┘  └─────────────────┘   │
└─────────────────┘     │                                         │
                        └─────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 EXTERNAL SERVICES                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ Tavily Web      │  │ Sentence Trans.  │  │ File Storage    │ │
│  │ Search API      │  │ Embeddings       │  │ (Local/S3)      │ │
│  │                 │  │                  │  │                 │ │
│  │ • Search        │  │ • MiniLM-L6-v2   │  │ • Uploads       │ │
│  │ • Snippets      │  │ • Fast Inference │  │ • Documents     │ │
│  │ • Direct Answer │  │ • Local Compute  │  │ • Backups       │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│          ENTERPRISE INFRASTRUCTURE & CI/CD LAYER               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ Harness CI/CD   │  │ Terraform IaC    │  │ Multi-Cloud     │ │
│  │ Pipeline        │  │                  │  │ Deployment      │ │
│  │                 │  │ • GCP Resources  │  │                 │ │
│  │ • Multi-Agent   │  │ • K8s Clusters   │  │ • Cloud Run     │ │
│  │   Testing       │  │ • State Mgmt     │  │ • Kubernetes    │ │
│  │ • Security Scan │  │ • Env Configs    │  │ • Auto-scaling  │ │
│  │ • Blue/Green    │  │ • Monitoring     │  │ • Load Balance  │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ Background      │  │ Observability    │  │ Security        │ │
│  │ Processing      │  │                  │  │                 │ │
│  │                 │  │ • OpenTelemetry  │  │ • Container Scan│ │
│  │ • Celery Workers│  │ • Structured Logs│  │ • Dependency    │ │
│  │ • Redis Queue   │  │ • Request IDs    │  │   Vulnerability │ │
│  │ • Progress      │  │ • Health Checks  │  │ • Rate Limiting │ │
│  │ • Task Status   │  │ • Metrics Export │  │ • Audit Logging │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Enterprise Database Architecture

### Multi-Database Strategy

The platform uses a specialized database approach optimized for enterprise scale:

- **MongoDB**: Document storage with full-text search, metadata indexing
- **PostgreSQL**: Transactional data, session management, audit trails, metrics
- **Redis**: High-performance caching, Celery message broker, session storage
- **Vector Database**: Multi-cloud abstraction for similarity search

### Vector Database Options

**1. Vertex AI (Google Cloud)**
- Native GCP integration with auto-scaling
- Advanced indexing with approximate nearest neighbors
- Production-ready with enterprise SLA

**2. Snowflake Cortex**
- Data warehouse + vector capabilities
- SQL-native vector operations with `VECTOR_COSINE_SIMILARITY`
- Perfect for analytics workloads

**3. CockroachDB (Bonus! 🎯)**
- SQL + vector capabilities in single database
- Global distribution with ACID transactions
- PostgreSQL compatibility with vector extension

**4. ChromaDB (Development)**
- Local development and testing
- Fast prototyping and evaluation

### Database Adapters (`src/app/database/`)

- **`mongodb_adapter.py`**: Async MongoDB operations with connection pooling
- **`postgres_adapter.py`**: Session management and metrics with asyncpg
- **`vector_adapters.py`**: Multi-cloud vector database abstraction
- **Factory Pattern**: Automatic adapter selection based on configuration

## Core Components

### 1. Document Management (`DocumentService`)
- **File Upload**: Validates file types (PDF, TXT, MD), size limits (10MB)
- **Text Extraction**: PDF parsing with pypdf, metadata preservation
- **Async Processing**: Background document ingestion via Celery workers
- **Storage**: Local file system with configurable upload directory

### 2. RAG Pipeline (`RAGService`)
- **Vector Store**: ChromaDB with persistent storage (`.rag_store/`)
- **Embeddings**: Sentence Transformers (`all-MiniLM-L6-v2`)
- **Chunking**: Recursive text splitting with overlap (800 words, 100 overlap)
- **Retrieval**: Semantic search with relevance scoring and source tracking
- **Caching**: In-memory embedding cache for duplicate content

### 3. Intelligent Agent (`AgentService`)
- **Routing Logic**: LangGraph-based decision tree
  - Internal documents preferred when relevance > 0.7
  - Web search for recency keywords (`latest`, `current`, `news`)
  - Context-aware routing based on conversation history
- **Source Integration**: Merges internal docs and web results with citations
- **Session Management**: Redis-backed conversation history (24h TTL)

### 4. AI Service Layer (`AIService`)
- **Multi-Provider**: OpenAI primary, Anthropic fallback
- **Structured Output**: Instructor integration for typed responses
- **Streaming**: Server-sent events for real-time responses
- **Error Handling**: Graceful degradation between providers

### 5. Chat Interface (`/chat/*`)
- **Unified Endpoint**: Single interface for all queries
- **Citation Support**: Links answers back to source documents
- **Session Continuity**: Conversation threads with memory
- **Response Formats**: JSON responses with sources or streaming text

## Data Flow

### Document Upload Flow
1. **Upload Request** → File validation (type, size, content)
2. **File Storage** → Saved with unique ID based on content hash
3. **Background Task** → Queued for async processing via Celery
4. **Text Extraction** → PDF/text parsing with error handling
5. **Chunking** → Recursive splitting with metadata preservation
6. **Embedding** → Vector generation with sentence transformers
7. **Storage** → ChromaDB persistence with source tracking
8. **Status Update** → Document marked as ready for querying

### Query Processing Flow
1. **Chat Request** → Question received with optional session ID
2. **Memory Retrieval** → Load conversation history from Redis
3. **Route Decision** → LangGraph workflow determines RAG vs Web
4. **Context Retrieval** → Vector search or web API call
5. **Source Tracking** → Metadata and relevance scores preserved
6. **Answer Generation** → LLM synthesis with citation instructions
7. **Response Formatting** → JSON with message, sources, routing info
8. **Memory Update** → Conversation saved for continuity

## Scalability Considerations

### Horizontal Scaling
- **Stateless API**: All session data in Redis enables multi-instance deployment
- **Background Workers**: Celery workers can be scaled independently
- **Load Balancing**: FastAPI instances behind reverse proxy (nginx/ALB)

### Performance Optimization
- **Embedding Cache**: In-memory cache reduces computation for duplicate content
- **Vector Search**: ChromaDB optimized for similarity search performance
- **Async Operations**: Non-blocking I/O for file uploads and LLM calls
- **Streaming**: Reduces perceived latency for long responses

### Resource Management
- **Memory**: Configurable chunk sizes and embedding dimensions
- **Storage**: Persistent ChromaDB with configurable retention
- **Rate Limiting**: Per-client request throttling (120/min default)
- **Request Size**: 2MB limit prevents resource exhaustion

## Security Architecture

### Input Validation
- **File Types**: Whitelist (PDF, TXT, MD only)
- **Content Scanning**: MIME type validation and size limits
- **Request Validation**: Pydantic models for all API inputs

### Access Control
- **Rate Limiting**: Redis-backed per-client throttling
- **Request Monitoring**: Structured logging with request IDs
- **Error Handling**: Safe error messages without information leakage

### Data Protection
- **Sensitive Data**: No hardcoded secrets, environment-based config
- **Audit Trail**: All document operations logged with metadata
- **Session Security**: TTL-based session expiration (24h default)

## Deployment Architecture

### Container Strategy
- **Multi-stage Builds**: Optimized Docker images for prod/dev/worker
- **Non-root Users**: Security hardening in production containers
- **Health Checks**: Built-in endpoint monitoring for orchestration

### Service Dependencies
- **Redis**: Session storage and Celery broker/result backend
- **ChromaDB**: Vector database with persistent volume mounts
- **File Storage**: Local volumes or S3-compatible object storage

### Monitoring & Observability
- **OpenTelemetry**: Distributed tracing for request flows
- **Structured Logging**: JSON logs with correlation IDs
- **Health Endpoints**: `/health` and `/ready` for load balancer checks
- **Metrics Export**: Performance and business metrics via OTEL

## Configuration Management

### Environment Variables
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional
OPENAI_API_KEY=sk-proj-...
REDIS_URL=redis://localhost:6379/0
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:14268/api/traces

# Performance Tuning
MAX_REQUEST_BODY_BYTES=10485760  # 10MB
RATE_LIMIT_REQUESTS_PER_WINDOW=120
AGENT_MEMORY_TTL_SECONDS=86400  # 24h
```

### Service Configuration
- **Model Selection**: Configurable LLM models per provider
- **Embedding Model**: Swappable sentence transformer models
- **Chunk Parameters**: Adjustable text splitting settings
- **Memory Limits**: Configurable conversation history length

This architecture provides a production-ready foundation for document Q&A with intelligent routing, comprehensive observability, and horizontal scalability.

## Multi-Agent Architecture Overview

The system now supports **four distinct agent architectures**, each optimized for different use cases and requirements:

### 1. LangGraph Agent (`/agent/chat`)
**Original workflow-based agent using LangChain/LangGraph**

```
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH AGENT                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐     │
│  │ Route Node  │───▶│  RAG Node    │───▶│  Web Node       │     │
│  │             │    │              │    │                 │     │
│  │ • Question  │    │ • Retrieve   │    │ • Tavily Search │     │
│  │ • Analysis  │    │ • Context    │    │ • Direct Answer │     │
│  │ • Decision  │    │ • Generation │    │ • Web Results   │     │
│  └─────────────┘    └──────────────┘    └─────────────────┘     │
│                                                                 │
│  StateGraph Workflow ────────────────────────────────────────── │
│  • Complex state management                                     │
│  • Conditional routing logic                                    │
│  • Multi-step workflows                                         │
└─────────────────────────────────────────────────────────────────┘
```

**Strengths**: Complex workflows, advanced state management, mature ecosystem
**Best For**: Multi-step processes, complex routing logic, existing LangChain integrations

### 2. Pydantic-AI Agent (`/pydantic-agent/chat`)
**Modern type-safe agent with structured output**

```
┌─────────────────────────────────────────────────────────────────┐
│                   PYDANTIC-AI AGENT                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐     │
│  │ Route Tool  │    │ Search Docs  │    │ Search Web      │     │
│  │             │    │ Tool         │    │ Tool            │     │
│  │ • Type Safe │    │              │    │                 │     │
│  │ • Validated │    │ • Structured │    │ • Structured    │     │
│  │ • Confident │    │ • Sources    │    │ • Citations     │     │
│  └─────────────┘    └──────────────┘    └─────────────────┘     │
│                                                                 │
│  Agent Framework ────────────────────────────────────────────── │
│  • Type-safe operations                                         │
│  • Structured output validation                                 │
│  • AG-UI compatibility                                          │
│  • FastAPI-like patterns                                        │
└─────────────────────────────────────────────────────────────────┘
```

**Strengths**: Type safety, structured output, modern patterns, AG-UI ready
**Best For**: Structured responses, type-safe applications, frontend integration

### 3. Hybrid Agent (`/hybrid-agent/chat`)
**Best of both worlds: LangGraph workflows + Pydantic-AI tools**

```
┌─────────────────────────────────────────────────────────────────┐
│                     HYBRID AGENT                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              LANGGRAPH WORKFLOW LAYER                      │ │
│  │                                                            │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │ │
│  │  │ Planning    │  │ RAG Exec     │  │ Web Exec        │    │ │
│  │  │ Node        │  │ Node         │  │ Node            │    │ │
│  │  └─────┬───────┘  └──────┬───────┘  └─────────┬───────┘    │ │
│  └────────┼────────────────┼──────────────────────┼───────────┘ │
│           │                │                      │             │
│  ┌────────▼────────────────▼──────────────────────▼───────────┐ │
│  │           PYDANTIC-AI TOOLS LAYER                          │ │
│  │                                                            │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │ │
│  │  │ Route Query │  │ Search Docs  │  │ Search Web      │    │ │
│  │  │ Tool        │  │ Tool         │  │ Tool            │    │ │
│  │  │ (Type Safe) │  │ (Structured) │  │ (Validated)     │    │ │
│  │  └─────────────┘  └──────────────┘  └─────────────────┘    │ │
│  └──────────────────────────────────────────────────────────-─┘ │
│                                                                 │
│  Integration Benefits ───────────────────────────────────────── │
│  • Complex workflow orchestration                               │
│  • Type-safe tool execution                                     │
│  • Structured output validation                                 │
│  • Migration-friendly approach                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Strengths**: Workflow control + type safety, enterprise-ready, migration-friendly
**Best For**: Production systems, complex requirements, gradual migrations

### 4. Smart Orchestrator (`/smart/chat`)
**Intelligent agent selection based on task analysis**

```
┌─────────────────────────────────────────────────────────────────┐
│                  SMART ORCHESTRATOR                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                  TASK ANALYZER                              ││
│  │                                                             ││
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐     ││
│  │  │ Complexity  │  │ Category     │  │ Context         │     ││
│  │  │ Assessment  │  │ Detection    │  │ Analysis        │     ││
│  │  │             │  │              │  │                 │     ││
│  │  │ Simple      │  │ • Q&A        │  │ • User Prefs    │     |│
│  │  │ Moderate    │  │ • Search     │  │ • Requirements  │     ││
│  │  │ Complex     │  │ • Analysis   │  │ • History       │     ││
│  │  │             │  │ • Workflow   │  │                 │     ││
│  │  └─────────────┘  └──────────────┘  └─────────────────┘     │|
│  └─────────────────────────┬───────────────────────────────────┘│
│                            │                                    │
│  ┌─────────────────────────▼───────────────────────────────────┐│
│  │               AGENT SELECTION LOGIC                         ││
│  │                                                             ││
│  │  Simple Q&A ────────────────▶ Pydantic-AI                   ││
│  │  Complex Workflow ──────────▶ LangGraph                     ││
│  │  Mixed Requirements ────────▶ Hybrid                        ││
│  │  Structured Output ─────────▶ Pydantic-AI                   ││
│  │  Unknown/Varied ────────────▶ Smart Routing + Fallbacks     ││
│  └─────────────────────────┬───────────────────────────────────┘│
│                            │                                    │
│  ┌─────────────────────────▼───────────────────────────────────┐│
│  │            EXECUTION WITH FALLBACKS                         ││
│  │                                                             ││
│  │  [Primary Agent] ──Error──▶ [Fallback 1] ──Error──▶ [FB 2]  ││
│  │                                                             ││
│  │  Orchestration Metadata:                                    ││
│  │  • Decision reasoning                                       ││
│  │  • Confidence scores                                        ││
│  │  • Agent used                                               ││
│  │  • Fallback history                                         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Strengths**: Automatic selection, task-aware routing, fallback mechanisms
**Best For**: General-purpose applications, varied workloads, user-facing systems

## Agent Selection Matrix

| Use Case | LangGraph | Pydantic-AI | Hybrid | Smart |
|----------|-----------|-------------|--------|-------|
| Simple Q&A | ⚠️ Overkill | ✅ Optimal | ⚠️ Overhead | ✅ Auto-routes |
| Complex Workflows | ✅ Optimal | ❌ Limited | ✅ Best | ✅ Auto-routes |
| Structured Output | ⚠️ Manual | ✅ Native | ✅ Validated | ✅ Auto-routes |
| Type Safety | ❌ Limited | ✅ Native | ✅ Tools only | ✅ Depends |
| Migration Path | ❌ Legacy | ❌ Rewrite | ✅ Gradual | ✅ Flexible |
| Enterprise | ✅ Proven | ⚠️ Newer | ✅ Robust | ✅ Adaptable |

## Integration Benefits

The multi-agent architecture provides:

1. **Flexibility**: Choose the right tool for each task
2. **Migration Path**: Gradual transition from LangGraph to modern patterns
3. **Future-Proofing**: Support for emerging patterns and requirements
4. **Performance**: Optimal agent selection reduces overhead
5. **Development Experience**: Type safety and modern tooling where appropriate
6. **Production Readiness**: Enterprise-grade reliability with fallback mechanisms

This comprehensive approach ensures the system can handle diverse requirements while maintaining performance, reliability, and developer experience.