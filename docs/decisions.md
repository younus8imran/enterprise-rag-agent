# Architecture Decision Records (ADR)

This document tracks significant architectural decisions.

## ADR Template
- **ID**: ADR-00X
- **Date**: YYYY-MM-DD
- **Status**: Proposed / Accepted / Superseded
- **Context**: What is the problem?
- **Decision**: What was chosen and why?
- **Consequences**: What are the trade-offs?

---

## ADR-001: Use of LangGraph for Orchestration
- **Status**: Accepted
- **Context**: The system requires cyclic workflows (e.g., the agent finds a gap in research and decides to search again). Standard linear chains are insufficient.
- **Decision**: Use LangGraph to define the agentic flow as a state machine.
- **Consequences**: Higher complexity in state management but enables true agentic behavior and better controllability.

## ADR-002: PostgreSQL + pgvector for Unified Storage
- **Status**: Accepted
- **Context**: Need to handle both structured SQL data and unstructured embeddings.
- **Decision**: Use PostgreSQL with the `pgvector` extension.
- **Consequences**: Simplifies infrastructure by using one database for both relational and vector data; leverages Postgres's robust security and ACID compliance.

## ADR-003: Hybrid Retrieval with Reciprocal Rank Fusion (RRF)
- **Status**: Accepted
- **Context**: Vector search is great for semantics but poor for exact keyword matches (e.g., specific product IDs).
- **Decision**: Combine pgvector (Cosine Similarity) and BM25 (Keyword) using RRF to merge results.
- **Consequences**: Increased latency due to two search passes, but significantly improved retrieval precision.

## ADR-004: Cross-Encoder Reranking
- **Status**: Accepted
- **Context**: Bi-Encoders (used in vector search) are fast but less precise.
- **Decision**: Use a Cross-Encoder model to rerank the top-k results from the hybrid search.
- **Consequences**: Slower inference time for the top-k candidates, but greatly reduces noise passed to the LLM.

## ADR-005: Row Level Security (RLS) for Multi-tenancy
- **Status**: Accepted
- **Context**: In an enterprise setting, strict data isolation between tenants is critical.
- **Decision**: Use PostgreSQL RLS based on a `tenant_id` session variable.
- **Consequences**: Moves security logic into the database layer, reducing the risk of application-level "leaky" queries.

## ADR-006: LLM-as-a-Judge for Retrieval Grading
- **Status**: Accepted
- **Context**: Traditional metrics (Precision@k) don't capture whether the context is *actually* useful for the specific query.
- **Decision**: Use a smaller, fast LLM to grade retrieved chunks as "Relevant" or "Irrelevant".
- **Consequences**: Adds an LLM call to the retrieval path, but prevents the final answer from being based on "hallucinated context".

## ADR-007: Redis for LangGraph State Persistence
- **Status**: Accepted
- **Context**: Agentic conversations can be long-running and need to survive API pod restarts.
- **Decision**: Use Redis as the checkpointer for LangGraph state.
- **Consequences**: Adds a dependency on Redis, but ensures seamless conversation continuity and scalability.

## ADR-008: JWT + bcrypt Auth (replacing mock Bearer)
- **Status**: Accepted
- **Date**: 2026-09-05
- **Context**: Production needs real user identity; mock `Bearer admin` tokens are unsuitable for multi-tenant access control.
- **Decision**: Use `pyjwt` for JWT creation/validation and `bcrypt` (via `passlib`) for password hashing. Tokens signed with `HS256` using `JWT_SECRET` env var (≥32 bytes). `TokenPayload.exp` stored as Unix `int` to match `jwt.decode` output. Swagger UI Authorize works with `Authorization: Bearer <token>`.
- **Consequences**: bcrypt is slow by design (resistant to brute force); tokens expire in 60 min. Requires `email-validator` for `EmailStr`.

## ADR-009: Mistral Embeddings (replacing MockEmbedder)
- **Status**: Accepted
- **Date**: 2026-09-05
- **Context**: `MockEmbedder` generates deterministic pseudo-vectors — fine for tests, useless for real semantic search.
- **Decision**: Swap to `MistralEmbedder` calling `https://api.mistral.ai/v1/embeddings` with `mistral-embed` model. Pluggable via `BaseEmbedder` interface; service/ingestion default to `MistralEmbedder`. `MockEmbedder` retained for unit tests.
- **Consequences**: Requires `MISTRAL_API_KEY` env var; adds network dependency per embed call. `httpx` already in deps.
