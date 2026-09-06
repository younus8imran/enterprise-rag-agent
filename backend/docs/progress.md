### Phase 1: Foundation (Completed)
- [x] Project structure and engineering context setup.
- [x] Docker environment (Postgres/pgvector) configuration.
- [x] Basic FastAPI skeleton.
- [x] Database connection pooling and migration strategy.

### Phase 2: Core RAG Implementation (Completed)
- [x] Database model for enterprise data (Customers, Products, Orders, etc.).
- [x] Synthetic data seeding script.
- [x] Read-only database role for SQL Agent.
- [x] Integration tests for database connectivity and security.

### Phase 3: Enterprise Document RAG (Completed)
- [x] Document and Chunk models with pgvector.
- [x] Hybrid Retrieval implementation (Vector + Keyword).
- [x] RRF and Reranking logic.
- [x] Metadata filtering foundation.
- [x] Real document ingestion pipeline: parse → chunk → embed → store
  (`app/services/rag/parsers/`, `chunkers/`, `embeddings/`, `ingestion.py`).
- [x] Pluggable embedder interface with deterministic `MockEmbedder`
  (1536-dim, unit-normalised, L2-normalised).
- [x] `/api/v1/documents/ingest` runs the pipeline end-to-end and persists
  real chunks to pgvector.

### Phase 4: Agentic RAG (Completed)
- [x] LangGraph stateful orchestration.
- [x] Typed AgentState and Node implementation.
- [x] Agent Graph with routing, grading, and retries.
- [x] Synthesis and Citation validation logic.

### Phase 5: SQL Intelligence (Completed)
- [x] Production-grade NL-to-SQL translation layer.
- [x] Safe execution sandbox with `SQLValidator` and read-only roles.
- [x] Self-correcting execution loop (max 2 retries).
- [x] Comprehensive security model and adversarial testing.

### Phase 6: Web Research Agent (Completed)
- [x] Provider-agnostic search abstraction.
- [x] Multi-query generation for complex questions.
- [x] Source ranking and deduplication.
- [x] Source-aware evidence model (Web, SQL, Internal, Inference).
- [x] Full citation preservation and markdown formatting.
- [x] Comprehensive test suite for research flow and evidence handling.
- [x] Concrete TavilySearchProvider implementation.
- [x] Robust confidence calculation and evidence validation.

### Phase 7: Full Agentic Research Orchestration (Completed)
- [x] Dynamic tool selection (RAG, SQL, Web)
- [x] Parallel tool execution when safe
- [x] Bounded retries and failure recovery
- [x] End-to-end tests for all tool combinations

### Phase 8: Enterprise Security (Completed)
- [x] Authentication and user identity
- [x] Authorization and access control
- [x] Document access levels and metadata filtering
- [x] SQL read-only access enforcement
- [x] Prompt injection defenses
- [x] Tool permission boundaries
- [x] Input and output validation
- [x] Security architecture documentation

### Phase 9: Evaluation Framework (Completed)
- [x] Comprehensive benchmark dataset (16 questions)
- [x] Retrieval metrics (hit rate, context precision)
- [x] Generation metrics (faithfulness, citation correctness)
- [x] Agent metrics (tool selection accuracy, task completion)
- [x] SQL metrics (validity, execution success)
- [x] Security metrics (adversarial blocking)
- [x] `make evaluate` command
- [x] Reproducible JSON reports

### Phase 10: Observability (Completed)
- [x] Request ID and context propagation
- [x] Comprehensive telemetry collection
- [x] Performance metrics (latency per component)
- [x] Token tracking and cost estimation
- [x] Structured JSON logging
- [x] OpenTelemetry-compatible tracing
- [x] Safe event exposure (no chain-of-thought)
- [x] Telemetry tests

### Phase 11: Production API (Completed)
- [x] POST /api/v1/chat
- [x] POST /api/v1/research
- [x] GET /api/v1/documents
- [x] POST /api/v1/documents/ingest
- [x] GET /api/v1/runs/{run_id}
- [x] GET /api/v1/health
- [x] Pydantic request/response schemas
- [x] Authentication middleware
- [x] Input validation
- [x] Proper HTTP status codes
- [x] Structured error responses
- [x] API versioning (/api/v1)
- [x] OpenAPI documentation
- [x] Streaming support for long-running tasks
- [x] API integration tests

## Current Status
- **Current Phase**: Production Hardening + Real Auth (COMPLETE).
- **Completed This Session**:
    - Real JWT auth (pyjwt + bcrypt); `TokenPayload.exp=int`; 45-char secret.
    - `/auth/login` → token; `/auth/me` → 200 via `HTTPBearer(auto_error=False)`.
    - Mistral embedder swapped for MockEmbedder in service.py + ingestion.py.
    - `email-validator` added to Dockerfile; `MISTRAL_API_KEY` set; `JWT_SECRET` ≥ 32 bytes.
    - `docker-compose.yml` overrides `DATABASE_URL` to `@db`; `.env` keeps `localhost` for local dev.
    - E2E verified: register → login → `/auth/me` (200) → `/chat` (200, citations).
    - `docs/decisions.md` ADR-008 (JWT) + ADR-009 (Mistral) added.
- **Remaining Work**: None (mock-removal + Mistral wire complete). Verify `/auth/me` token refresh and `/chat` synthesis with Mistral.
- **Next Recommended Task**: Production security review (`/security-review`) + run full `pytest`.

## Known Bugs
- None.

## Technical Debt
- Chat endpoint (`stream_agent_events`) returns mock data; LangGraph not yet wired.
- ResearchAgent uses `MockSearchProvider` (not Tavily).

## Next Recommended Task
- Wire Mistral embedder + Mistral chat completions into the RAG service and agent.
