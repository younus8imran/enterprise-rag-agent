# CLAUDE.md

## Project Purpose
Enterprise Agentic RAG + Research + SQL Platform: A production-grade system capable of performing complex research, executing precise SQL queries over enterprise data, and retrieving information via advanced RAG, all orchestrated by an agentic framework.

## Architecture Principles
- **Modular Orchestration**: Use LangGraph for stateful, cyclic agentic workflows.
- **Security-First**: Zero-trust approach to LLM-generated SQL and prompt inputs.
- **Evaluatable by Design**: Every component must have a corresponding evaluation metric.
- **Observability**: Full traceability of agentic reasoning steps (traces, spans).
- **Async-First**: High-concurrency FastAPI architecture for enterprise scale.

## Technology Choices
- **Language**: Python 3.11+ (Strict typing with Mypy)
- **Framework**: FastAPI
- **Orchestration**: LangGraph / LangChain
- **Database**: PostgreSQL with `pgvector`
- **Environment**: Docker / Docker Compose
- **Testing**: Pytest
- **Evaluation**: RAGAS / LLM-as-a-Judge

## Coding Standards
- **Style**: PEP 8 compliant.
- **Typing**: Mandatory type hints for all function signatures.
- **Pattern**: Dependency Injection for services and database sessions.
- **Async**: Use `async`/`await` for all I/O bound operations.
- **Documentation**: Google-style docstrings for public APIs.

## Security Requirements
- **SQL Injection**: Mandatory use of parameterized queries or ORM; no raw f-string SQL.
- **Prompt Injection**: Input sanitization and system prompt hardening.
- **Data Isolation**: Multi-tenant architecture with strict row-level security (RLS) or schema separation.
- **Secrets**: No secrets in code; use environment variables via Pydantic Settings.

## Testing Requirements
- **Unit Tests**: $\geq 80\%$ coverage for core business logic.
- **Integration Tests**: Mandatory for pgvector and LangGraph state transitions.
- **E2E Tests**: Critical paths (Research $\rightarrow$ SQL $\rightarrow$ Answer) must be automated.

## Evaluation Requirements
- **RAG Metrics**: Faithfulness, Answer Relevance, Context Precision.
- **SQL Metrics**: Execution accuracy, Schema adherence.
- **Research Metrics**: Source diversity, Factuality.

## Commands to Run
- **Install**: `pip install -r requirements.txt`
- **Run App**: `fastapi dev main.py`
- **Run Tests**: `pytest`
- **Lint**: `flake8 .`
- **Type Check**: `mypy .`
- **Infrastructure**: `docker-compose up -d`

## Definition of Done (DoD)
- [ ] Code passes all linting and type checks.
- [ ] All unit and integration tests pass.
- [ ] Security review completed (`/security-review`).
- [ ] Evaluation scores meet the baseline for the feature.
- [ ] `docs/progress.md` and `docs/decisions.md` updated.
- [ ] Documentation reflects the current implementation.

## Instructions
**IMPORTANT**: Before continuing any work, always inspect `docs/progress.md` to align with the current phase and next recommended tasks.
