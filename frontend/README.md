# Frontend — Enterprise Intelligence Agent

React + Vite SPA for the Enterprise Agentic RAG + Research + SQL Platform.

## Tech Stack

- **Framework**: React 18 (TypeScript)
- **Build Tool**: Vite
- **Routing**: React Router v6
- **Styling**: CSS (plain)

## Project Structure

```
frontend/
├── public/
├── src/
│   ├── api/              # API client functions (auth, chat, documents, etc.)
│   ├── components/       # Reusable UI components
│   ├── context/          # React context providers (auth context)
│   ├── pages/            # Page-level components
│   ├── routes/           # Route definitions
│   ├── App.tsx           # Root component
│   └── main.tsx         # Entry point
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
└── README.md
```

## Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Run the development server

```bash
npm run dev
```

Frontend starts at `http://localhost:5173`.

### 3. Build for production

```bash
npm run build
```

Preview production build:

```bash
npm run preview
```

## Configuration

The frontend expects the backend API at `http://localhost:8000`. To change the API base URL, update the `baseUrl` in the API client files under `src/api/`.

## Features

- **Authentication**: Register, login, logout with JWT tokens
- **Chat Interface**: Real-time chat with the agent
- **Document Management**: Upload and manage documents for RAG
- **Research**: Run research queries against the web
- **SQL Explorer**: Execute validated SQL queries against enterprise data
- **Chat History**: Persistent conversation history per user

## API Integration

The frontend communicates with the backend REST API under `/api/v1/`. All protected routes require a Bearer token obtained from login.

Example authenticated request:

```typescript
const response = await fetch(`${API_BASE}/chat`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  },
  body: JSON.stringify({ message: '...' }),
});
```

## Environment Variables

Create a `.env` file if needed:

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend API base URL |
