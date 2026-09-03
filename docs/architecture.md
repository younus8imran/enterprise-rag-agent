# Comprehensive System Architecture

This document defines the architectural blueprint for the Enterprise Intelligence Agent.

## 1. System Architecture
The system is a distributed agentic platform where the reasoning logic is decoupled from the execution tools.

```mermaid
graph TD
    User((User)) --> API[FastAPI Gateway]
    
    subgraph "Orchestration Layer"
        API --> LG[LangGraph Orchestrator]
        LG --> State[(Redis State Store)]
    end
    
    subgraph "Execution Agents"
        LG --> RAG[RAG Agent]
        LG --> SQL[SQL Agent]
        LG --> RS[Research Agent]
    end
    
    subgraph "Data Layer"
        RAG --> PGV[(Postgres + pgvector)]
        SQL --> PG[(Postgres Relational)]
        RS --> Web[Web Search API]
    end
    
    subgraph "Quality & Security"
        LG --> Critic[Critic Node]
        LG --> Sec[Security Middleware]
        RAG --> Eval[Evaluation Engine]
    end
    
    Critic --> LG
    Sec --> API
```

## 2. Component Architecture
The system is divided into four primary modules:

- **API Gateway**: Handles AuthN/AuthZ, Rate Limiting, and WebSocket streaming.
- **Agentic Core (LangGraph)**: Manages the conversation state, routing logic, and iterative loops.
- **Tool Layer**: Specialized executors for Vector Retrieval, SQL execution, and Web Research.
- **Observability & Eval**: Tracks spans via OpenTelemetry and scores outputs via RAGAS.

## 3. Agent Graph (LangGraph)
The agentic flow is a cyclic graph that ensures quality via a Critic loop.

```mermaid
graph TD
    Start((Start)) --> Rewrite[Query Rewriter]
    Rewrite --> Router{Router}
    
    Router -->|Unstructured| RAG[RAG Pipeline]
    Router -->|Structured| SQL[SQL Pipeline]
    Router -->|External| RS[Research Pipeline]
    
    RAG --> Synth[Synthesizer]
    SQL --> Synth
    RS --> Synth
    
    Synth --> Critic{Critic}
    Critic -->|Needs Refinement| Router
    Critic -->|Approved| Citations[Citation Validator]
    
    Citations --> End((End))
```

## 4. Database Schema
We use a unified PostgreSQL instance for both relational and vector data.

### Relational Schema
- `tenants`: `id, name, created_at, plan_level`
- `users`: `id, tenant_id, email, role, hashed_password`
- `documents`: `id, tenant_id, filename, metadata, created_at`
- `chunks`: `id, doc_id, content, embedding (vector), created_at`
- `queries`: `id, tenant_id, user_id, input, output, score, timestamp`

### Vector Indexing
- **Index**: HNSW (Hierarchical Navigable Small World)
- **Distance Metric**: Cosine Similarity
- **Isolation**: Row Level Security (RLS) on `tenant_id`.

## 5. Retrieval Pipeline (RAG)
A high-precision pipeline to eliminate noise and hallucinations.

```mermaid
graph LR
    Q[Query] --> RW[Query Rewrite]
    RW --> Hybrid[Hybrid Search]
    
    subgraph "Hybrid Search"
        Hybrid --> BM25[BM25 Keyword]
        Hybrid --> Vec[pgvector Semantic]
        BM25 --> RRF[Reciprocal Rank Fusion]
        Vec --> RRF
    end
    
    RRF --> Rerank[Cross-Encoder Reranker]
    Rerank --> Grade[LLM Relevance Grader]
    Grade --> TopK[Filtered Top-K Context]
```

## 6. SQL-Agent Pipeline
A safe, iterative process for translating natural language to enterprise data.

```mermaid
graph TD
    Q[Query] --> Schema[Schema Analyzer]
    Schema --> Gen[SQL Generator]
    Gen --> Val[SQL Validator]
    
    Val -->|Invalid| Gen
    Val -->|Valid| Exec[Safe Executor]
    
    Exec --> Result[Result Formatter]
    Result --> Synth[Synthesizer]
```

## 7. Research Pipeline
Iterative discovery for information not present in internal documents.

```mermaid
graph TD
    Q[Query] --> Plan[Research Plan]
    Plan --> Search[Web Search Tool]
    Search --> Scrape[Page Scraper]
    Scrape --> Analyze[Content Analyzer]
    
    Analyze --> Gap{Gap Found?}
    Gap -->|Yes| Search
    Gap -->|No| Synthesis[Research Synthesis]
```

## 8. Security Architecture
Defense-in-depth for enterprise data.

- **Authentication**: OAuth2 / JWT with FastAPI Security.
- **Authorization**: RBAC (Role-Based Access Control).
- **Data Isolation**: PostgreSQL RLS.
  - Every query is prefixed with `SET app.current_tenant = 'tenant_id'`.
- **SQL Sandbox**:
  - Read-only database user for the SQL Agent.
  - Query timeout (e.g., 5s) and row limits.
- **Prompt Hardening**: System prompt delimiters and input sanitization to prevent prompt injection.

## 9. Evaluation Architecture
Quantitative measurement of agentic performance.

```mermaid
graph TD
    Dataset[(Gold Dataset)] --> Pipeline[Agent Pipeline]
    Pipeline --> Output[Agent Output]
    
    Output --> RAGAS[RAGAS Metrics]
    Output --> Judge[LLM-as-a-Judge]
    
    RAGAS --> Score[Faithfulness/Relevance]
    Judge --> Score
    
    Score --> Dashboard[Performance Dashboard]
```

## 10. Deployment Architecture
Scalable, containerized infrastructure.

```mermaid
graph TD
    LB[Load Balancer] --> API[FastAPI Pods]
    API --> Redis[(Redis - State)]
    API --> PG[(Postgres - Data)]
    API --> LLM[Claude API]
    
    subgraph "Observability"
        API --> OTEL[OpenTelemetry]
        OTEL --> Jaeger[Jaeger/Grafana]
    end
    
    subgraph "Infrastructure"
        PG --> Vol[(Persistent Volume)]
    end
```
