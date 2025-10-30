# Doc-QA Assistant Capstone Project

## Overview
A production-ready document Q&A assistant that allows teams to upload documents, ask questions about them, and get AI-powered responses that can intelligently route between internal knowledge and web search.

## Core Features

### 1. Document Management
- **Upload API**: `/docs/upload` - accepts PDF, TXT, MD files with validation
- **Document metadata**: track source, upload time, processing status
- **Async processing**: background document chunking and embedding via Celery
- **Progress tracking**: real-time status updates during ingestion

### 2. Intelligent Chat Interface  
- **Unified endpoint**: `/chat` - single interface for all queries
- **Agent routing**: automatically decides between RAG and web search
- **Session management**: persistent conversation history with Redis
- **Streaming responses**: real-time answer generation with reasoning breadcrumbs

### 3. Enhanced RAG Pipeline
- **Smart chunking**: recursive text splitting with metadata preservation
- **Rich context**: include document source, section, and confidence scores
- **Semantic search**: improved retrieval with relevance scoring
- **Citation support**: link answers back to source documents

### 4. Production Features
- **Async jobs**: long-running uploads and queries return task_id
- **Observability**: OpenTelemetry traces for document processing pipeline
- **Security**: file type validation, size limits, sanitization
- **Rate limiting**: protect against abuse while maintaining UX

## Technical Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Upload    │────│  Background  │────│   Vector    │
│  Endpoint   │    │  Processing  │    │   Store     │
└─────────────┘    └──────────────┘    └─────────────┘
       │                   │                   │
       │            ┌─────────────┐           │
       └────────────│    Redis    │───────────┘
                    │  (Queue +   │
                    │   Memory)   │
                    └─────────────┘
                           │
                    ┌─────────────┐
                    │    Chat     │
                    │   Agent     │────→ Web Search
                    │             │
                    └─────────────┘
                           │
                    ┌─────────────┐
                    │  Response   │
                    │  Streaming  │
                    └─────────────┘
```

## Implementation Plan

### Phase 1: Document Upload & Processing
1. Create `/docs/upload` endpoint with file validation
2. Enhance `RAGService` for document metadata and chunking
3. Build async document processing task with progress updates
4. Add document management endpoints (list, status, delete)

### Phase 2: Enhanced Chat Experience
1. Upgrade agent to prefer internal docs over web when available
2. Add citation support to link answers to source documents
3. Implement conversation threading and context
4. Enhanced streaming with processing steps

### Phase 3: Production Polish
1. Add comprehensive error handling and validation
2. Performance optimization (caching, batch processing)
3. Security hardening (file scanning, input sanitization)
4. Monitoring and alerting integration

### Phase 4: Demo & Documentation
1. Create sample document set for demonstration
2. Record demo video showing upload → chat → citations
3. Generate architecture diagrams and API documentation
4. Run comprehensive evaluation and capture metrics

## Success Criteria

### Functional Requirements
- [ ] Upload common document formats (PDF, TXT, MD)
- [ ] Async processing with real-time progress
- [ ] Intelligent routing between docs and web
- [ ] Persistent chat sessions with history
- [ ] Source citations in responses
- [ ] Docker deployment ready

### Quality Metrics
- [ ] RAG evaluation scores (precision, recall, relevance)
- [ ] Response latency < 2s for most queries
- [ ] Upload processing < 30s for typical documents
- [ ] 95% uptime with proper error handling
- [ ] Security scan passing with no high vulnerabilities

### Portfolio Artifacts
- [ ] 2-3 minute demo video
- [ ] Architecture diagram
- [ ] Performance benchmarks
- [ ] Sample Q&A dataset with citations
- [ ] Deployment guide

## Next Steps
1. Start with document upload infrastructure
2. Build on existing RAG and agent foundations
3. Focus on user experience and reliability
4. Capture metrics throughout development

---
*Target timeline: 1 week focused development*