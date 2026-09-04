# Enterprise Agentic RAG + Research + SQL Platform

A production-grade system for complex research, precise SQL queries over enterprise data, and advanced RAG orchestrated by an agentic framework.

## Architecture Principles

| Principle | Description |
|---|---|
| **Modular Orchestration** | LangGraph for stateful, cyclic agentic workflows |
| **Security-First** | Zero-trust approach to LLM-generated SQL and prompt inputs |
| **Evaluatable by Design** | Every component has a corresponding evaluation metric |
| **Observability** | Full traceability of agentic reasoning steps (traces, spans) |
| **Async-First** | High-concurrency FastAPI architecture for enterprise scale |

## Technology Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.11+ (Strict typing with Mypy) |
| **Framework** | FastAPI |
| **Orchestration** | LangGraph / LangChain |
| **Database** | PostgreSQL with `pgvector` |
| **Container** | Docker / Docker Compose |
| **Testing** | Pytest |
| **Evaluation** | RAGAS / LLM-as-a-Judge |

## Setup and Run on Local

### 1. Clone and enter the project
```bash
git clone <repo-url>
cd enterprise-intelligence-agent
```

### 2. Create environment file
```bash
cp .env.example .env
# Edit .env with your database URL, API keys, and secrets
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Start infrastructure (PostgreSQL + pgvector)
```bash
docker-compose up -d
```

### 5. Apply database migrations
```bash
alembic upgrade head
```

### 6. Seed synthetic data (optional)
```bash
python scripts/seed_database.py
```

### 7. Run the FastAPI server
```bash
fastapi dev main.py
```
The server starts at `http://localhost:8000` by default.

### 8. Run tests
```bash
pytest
```

### 9. Lint and type-check
```bash
flake8 .
mypy .
```

### 10. Evaluate the system
```bash
make evaluate
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start infrastructure (Postgres, etc.)
docker-compose up -d

# Run the app
fastapi dev main.py

# Run tests
pytest

# Lint
flake8 .

# Type check
mypy .

# Evaluate
make evaluate
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/chat` | POST | Chat with the agent |
| `/api/v1/research` | POST | Run research agent |
| `/api/v1/documents` | GET | List documents |
| `/api/v1/documents/ingest` | POST | Ingest new documents |
| `/api/v1/runs/{run_id}` | GET | Get run status |
| `/api/v1/health` | GET | Health check |

## Current Status

- **Phases 1–11**: All completed
- **Current Phase**: Transitioning to Full System Integration
- **Remaining Work**:
  - Complete Phase 3 Document Ingestion pipeline (parsing, chunking)
  - Integrate SQL agent into main LangGraph orchestration
  - Integrate Web Research agent into main LangGraph orchestration
  - End-to-end verification of hybrid (RAG + SQL + Web) flow

## Known Issues

- RAGService uses mocks for embeddings (testing without API keys)
- ResearchAgent uses a mock provider for testing

## Development

| Command | Purpose |
|---|---|
| `pip install -r requirements.txt` | Install dependencies |
| `fastapi dev main.py` | Start development server |
| `pytest` | Run test suite |
| `flake8 .` | Linting |
| `mypy .` | Type checking |
| `docker-compose up -d` | Start infrastructure |

## Evaluation Framework

- **RAG Metrics**: Faithfulness, Answer Relevance, Context Precision
- **SQL Metrics**: Execution accuracy, Schema adherence
- **Research Metrics**: Source diversity, Factuality
- **make evaluate** command runs full benchmark suite
- JSON reports stored in `reports/` directory

## Security

- **SQL Injection**: Mandatory parameterized queries or ORM; no raw f-string SQL
- **Prompt Injection**: Input sanitization and system prompt hardening
- **Data Isolation**: Multi-tenant architecture with strict row-level security (RLS) or schema separation
- **Secrets**: No secrets in code; use environment variables via Pydantic Settings

## License

MIT