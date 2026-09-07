# Backend — Enterprise Intelligence Agent

FastAPI backend for the Enterprise Agentic RAG + Research + SQL Platform.

## Tech Stack

- **Framework**: FastAPI (async)
- **ORM**: SQLAlchemy (async with `asyncpg`)
- **Migrations**: Alembic
- **Database**: PostgreSQL with `pgvector`
- **Cache**: Redis
- **Auth**: JWT (`pyjwt` + `passlib`)
- **Rate Limiting**: `slowapi`
- **LLM**: Mistral API
- **Research**: Tavily API

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/     # Route handlers (auth, chat, research, documents, sql, runs, health)
│   │   └── router.py      # API router aggregation
│   ├── core/
│   │   ├── config.py      # Pydantic settings (from .env)
│   │   ├── security.py    # JWT utils, password hashing
│   │   ├── exceptions.py  # Custom AppBaseException
│   │   └── logging.py    # Structured logging setup
│   ├── db/
│   │   ├── base.py        # SQLAlchemy declarative base
│   │   ├── session.py     # Async session factory
│   │   ├── connection.py  # DB engine setup
│   │   └── models/        # SQLAlchemy models (User, Run, Document, ChatMessage)
│   ├── services/          # Business logic (AuthService, ResearchService, etc.)
│   ├── main.py            # FastAPI app entrypoint
│   └── dependencies.py     # Shared FastAPI dependencies
├── alembic/
│   ├── env.py
│   └── versions/          # Database migration scripts
├── scripts/
│   └── seed_database.py   # Synthetic data seeder
├── tests/                 # Pytest unit/integration tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

### 1. Start infrastructure

```bash
docker compose up -d
```

Starts PostgreSQL (port 5432), Redis (port 6380), and the app container.

### 2. Install dependencies

```bash
uv pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your database URL, API keys, and secrets
```

Required environment variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `POSTGRES_USER` | PostgreSQL username |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `POSTGRES_DB` | PostgreSQL database name |
| `POSTGRES_SERVER` | PostgreSQL host |
| `REDIS_HOST` | Redis host |
| `REDIS_PORT` | Redis port (default 6379) |
| `JWT_SECRET` | Secret key for signing JWTs (must be overridden!) |
| `MISTRAL_API_KEY` | Mistral API key for LLM calls |
| `TAVILY_API_KEY` | Tavily API key for web research |

### 4. Run migrations

```bash
alembic upgrade head
```

### 5. (Optional) Seed data

```bash
python scripts/seed_database.py
```

### 6. Run the server

Development:
```bash
fastapi dev app.main:app --reload
```

The server starts at `http://localhost:8000`. API docs at `http://localhost:8000/api/v1/docs`.

## Docker

```bash
docker compose up --build
```

## Testing

```bash
pytest
```

## Linting & Type Checking

```bash
flake8 .
mypy .
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

JWT-based. All protected endpoints require:

```
Authorization: Bearer <access_token>
```

Token is obtained from `POST /api/v1/auth/login`. Contains `user_id` (int), `username`, and `role`.

## Architecture Notes

- **JWT `sub` claim**: Stored as string in token per JWT spec; decoded to `int` for database operations.
- **User scope**: `user_id` on `Run`, `ChatMessage`, and `Document` tables enforces user-scoped data isolation.
- **Async**: All database and HTTP operations use `async`/`await`.
- **Migrations**: Always use `alembic upgrade head`; never modify migrations that have been applied to shared environments.
