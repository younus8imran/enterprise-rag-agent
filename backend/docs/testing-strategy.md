# Testing Strategy

## Testing Pyramid
We follow a strict testing pyramid to ensure stability and correctness.

### 1. Unit Tests (Fastest)
- **Focus**: Pure functions, utility classes, individual LangGraph nodes.
- **Tool**: `pytest`
- **Goal**: Exhaustive edge-case coverage.

### 2. Integration Tests
- **Focus**: Database queries, `pgvector` search, external API calls (mocked).
- **Tool**: `pytest` with `testcontainers` or dedicated Docker test DB.
- **Goal**: Verify that components work together correctly.

### 3. State Transition Tests (LangGraph)
- **Focus**: Verifying the agent moves from state A to state B based on specific inputs.
- **Tool**: Custom graph testers.
- **Goal**: Ensure the agentic logic doesn't enter infinite loops or dead ends.

### 4. End-to-End (E2E) Tests (Slowest)
- **Focus**: Full request-response cycles from API to Database and back.
- **Tool**: `pytest` + `httpx`.
- **Goal**: Verify critical user paths.

## Test Case Management
All critical test cases are tracked in `tests/tests.json` to ensure visibility into coverage and status.
