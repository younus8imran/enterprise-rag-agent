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

## Project Structure

```
backend/          # FastAPI app + Alembic migrations + Docker
frontend/         # React + Vite SPA
uploads/          # User-uploaded documents
```

## Setup and Run

### 1. Clone and enter the project
```bash
git clone <repo-url>
cd enterprise-intelligence-agent
```

### 2. Start infrastructure (PostgreSQL + pgvector)
```bash
cd backend
docker compose up -d
```

### 3. Install Python dependencies
```bash
uv pip install -r requirements.txt
```

### 4. Create environment file
```bash
cp .env.example .env
# Edit .env with your database URL, API keys, and secrets
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
fastapi dev app.main:app --reload
```
The server starts at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### 8. Run the Frontend
```bash
cd ../frontend
npm install
npx vite
```
Frontend at `http://localhost:5173`.

### 9. Run tests
```bash
cd backend
pytest
```

### 10. Lint and type-check
```bash
flake8 .
mypy .
```

## Quick Start (Docker)

```bash
cd backend
docker compose up --build
```

## API Endpoints

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/v1/auth/register` | POST | — | Register new user |
| `/api/v1/auth/login` | POST | — | Login, returns JWT |
| `/api/v1/auth/me` | GET | Bearer | Get current user |
| `/api/v1/chat` | POST | Bearer | Chat with the agent |
| `/api/v1/chat/history` | GET | Bearer | Get chat history |
| `/api/v1/research` | POST | Bearer | Run research agent |
| `/api/v1/documents` | GET/POST | Bearer | List/ingest documents |
| `/api/v1/sql` | POST | Bearer | Execute validated SQL |
| `/api/v1/runs/{run_id}` | GET | Bearer | Get run status |
| `/api/v1/health` | GET | — | Health check |

## Authentication

JWT-based authentication. All protected endpoints require:
```
Authorization: Bearer <access_token>
```

Token is obtained from `POST /auth/login`. Contains `user_id` (int), `username`, `role`, and `tenant_id`.

## Development Notes

- **JWT**: `sub` claim stored as string in token (JWT spec), decoded to `int` for database operations.
- **Telemetry**: `user_id` and `tenant_id` typed as `int` throughout.
- **Database**: All foreign keys (`user_id`, `tenant_id`) use `INTEGER` columns.
