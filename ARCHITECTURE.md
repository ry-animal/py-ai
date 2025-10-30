# Doc-QA Assistant Architecture

## System Overview

The Doc-QA Assistant is a production-ready AI-powered document question-answering system that intelligently routes queries between internal knowledge base and external web search, providing cited responses with conversation continuity.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT INTERFACE                         │
├─────────────────────────────────────────────────────────────────┤
│  • HTTP API (FastAPI)                                           │
│  • Interactive Documentation (/docs)                            │
│  • Streaming & Non-streaming Chat                               │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│                    API GATEWAY LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  • CORS Middleware                                              │
│  • Rate Limiting (120 req/min per client)                       │
│  • Request Size Limits (2MB max)                                │
│  • Request ID Tracking & Logging                                │
│  • OpenTelemetry Instrumentation                                │
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
│   AGENT CORE    │     │           DATA LAYER                    │
├─────────────────┤     ├─────────────────────────────────────────┤
│                 │     │                                         │
│ ┌─────────────┐ │     │  ┌─────────────┐  ┌─────────────────┐   │
│ │ LangGraph   │ │     │  │ RAGService  │  │  ChromaDB       │   │
│ │ Workflow    │ │     │  │             │  │  (Vector Store) │   │
│ │             │ │     │  │ • Chunking  │  │                 │   │
│ │ ┌─────────┐ │ │     │  │ • Embedding │  │ • Embeddings    │   │
│ │ │  Route  │ │ │     │  │ • Retrieval │  │ • Metadata      │   │
│ │ │  Node   │ │ │◄────┤  │ • Citations │  │ • Persistence   │   │
│ │ └─────────┘ │ │     │  └─────────────┘  └─────────────────┘   │
│ │      │      │ │     │                                         │
│ │ ┌─────▼───┐ │ │     │  ┌─────────────┐  ┌─────────────────┐   │
│ │ │   RAG   │ │ │     │  │ AgentMemory │  │     Redis       │   │
│ │ │  Node   │ │ │     │  │             │  │  (Sessions)     │   │
│ │ └─────────┘ │ │     │  │ • Sessions  │  │                 │   │
│ │      │      │ │     │  │ • History   │  │ • Chat History  │   │
│ │ ┌─────▼───┐ │ │     │  │ • TTL       │  │ • TTL (24h)     │   │
│ │ │   Web   │ │ │     │  └─────────────┘  └─────────────────┘   │
│ │ │  Node   │ │ │     │                                         │
│ │ └─────────┘ │ │     └─────────────────────────────────────────┘
│ └─────────────┘ │
└─────────────────┘
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
│               INFRASTRUCTURE LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ Background      │  │ Observability    │  │ Security        │ │
│  │ Processing      │  │                  │  │                 │ │
│  │                 │  │ • OpenTelemetry  │  │ • FileValidation│ │
│  │ • Celery Workers│  │ • Structured Logs│  │ • Rate Limiting │ │
│  │ • Redis Queue   │  │ • Request IDs    │  │ • Input Sanitize│ │
│  │ • Progress      │  │ • Health Checks  │  │ • Error Handling│ │
│  │ • Task Status   │  │ • Metrics Export │  │ • Audit Logging │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

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