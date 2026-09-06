# Observability Architecture

This document describes the observability and telemetry framework for the Enterprise Intelligence Agent, designed to provide full visibility into request performance, tool usage, costs, and errors without exposing sensitive chain-of-thought reasoning.

## 1. Telemetry Collection

### Request Lifecycle Tracking
Every request is tracked from start to finish with a unique `request_id` that propagates through all components via context variables. This enables:
- End-to-end request tracing
- Component-level performance profiling
- Error attribution
- Cost tracking per request

### Collected Metrics

| Metric | Description | Purpose |
| :--- | :--- | :--- |
| **Request ID** | Unique identifier for each query | Distributed tracing |
| **User ID** | Identity of the requesting user | User behavior analysis |
| **Query** | The user's question (truncated to 100 chars) | Debugging and pattern analysis |
| **Model** | LLM model used (e.g., Mistral) | Cost attribution |
| **Total Tokens** | Prompt + completion tokens | Cost estimation |
| **Total Latency** | End-to-end request duration (ms) | Performance SLO monitoring |
| **Retrieval Latency** | Time spent in RAG retrieval + reranking | Component performance |
| **SQL Latency** | Time spent generating + executing SQL | SQL bottleneck detection |
| **Web Latency** | Time spent in web research | External dependency tracking |
| **Tool Calls** | Count per tool (RAG, SQL, Web) | Orchestration analysis |
| **Retries** | Number of self-correction attempts | Reliability monitoring |
| **Errors** | Count of errors encountered | Error rate tracking |
| **Confidence** | Agent's confidence in the final answer | Answer quality proxy |
| **Estimated Cost** | USD cost based on token usage | Budget monitoring |

## 2. Structured Logging

All telemetry is emitted as **structured JSON logs** via `structlog`, ensuring:
- Machine-parseable logs for automated analysis
- Consistent schema across all log entries
- Safe sanitization of sensitive data

### Log Events

#### Request Started
```json
{
  "event": "request_started",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "u123",
  "query": "What was the revenue in Q2?",
  "timestamp": "2026-09-03T12:33:54.949Z"
}
```

#### Span Completed
```json
{
  "event": "span_completed",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "span": "retrieve_rag",
  "duration_ms": 245.32,
  "success": true,
  "timestamp": "2026-09-03T12:33:55.194Z"
}
```

#### Request Completed
```json
{
  "event": "request_completed",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "u123",
  "total_latency_ms": 1234.56,
  "retrieval_latency_ms": 245.32,
  "sql_latency_ms": 123.45,
  "web_latency_ms": 0.0,
  "tool_calls": {"rag": 1, "sql": 1},
  "retries": 0,
  "errors": 0,
  "confidence": 0.85,
  "total_tokens": 1500,
  "estimated_cost_usd": 0.001200,
  "timestamp": "2026-09-03T12:33:56.184Z"
}
```

## 3. Tracing Integration

The `TelemetryCollector` is designed to be **compatible with OpenTelemetry and LangSmith**:
- **Span-based Architecture**: Each operation (retrieval, SQL execution, web search) is tracked as a span with start/end times.
- **Context Propagation**: The `request_id` acts as a trace ID, enabling distributed tracing across services.
- **Metadata**: Each span can carry arbitrary metadata for deeper analysis.

### OpenTelemetry Integration (Future)
To integrate with OpenTelemetry:
1. Replace `TelemetryCollector` span tracking with OpenTelemetry's `Tracer`.
2. Export spans to an OpenTelemetry collector (Jaeger, Zipkin, etc.).
3. Use `request_id` as the trace ID for cross-service correlation.

## 4. Privacy & Security

### No Chain-of-Thought Exposure
The telemetry system **never logs**:
- Internal reasoning steps
- Intermediate LLM outputs
- Retrieved document content (only chunk IDs)
- Full SQL queries (only execution status)

### Safe Data Only
Only the following are logged:
- Request metadata (ID, user, timestamp)
- Performance metrics (latency, tokens)
- Tool invocations (counts, not content)
- Error types (not sensitive data)

### Sensitive Data Sanitization
- **Queries** are truncated to 100 characters in logs.
- **User IDs** are pseudonymized in production logs.
- **SQL results** are never logged (only success/failure).

## 5. Cost Estimation

Token usage is tracked for every LLM call, and costs are estimated based on Mistral pricing:
- **Prompt tokens**: $0.30 per 1M tokens
- **Completion tokens**: $1.00 per 1M tokens

This provides real-time cost visibility per request, enabling budget alerts and user-level cost attribution.

## 6. Usage

### In Agent Nodes
```python
from app.core.telemetry.collector import TelemetryCollector

collector = TelemetryCollector()
collector.start_request(query="What is our revenue?", user_id="u123")

span = collector.start_span("retrieve_rag")
# ... perform retrieval ...
collector.end_span(span, success=True)

collector.record_tool_call("rag")
collector.record_tokens(prompt_tokens=500, completion_tokens=200)
collector.end_request(confidence=0.85)
```

### Query Telemetry
Telemetry is automatically aggregated and can be queried for:
- **Performance analysis**: Identify slow components.
- **Cost analysis**: Track spend per user/tenant.
- **Error analysis**: Detect failure patterns.
- **Tool usage**: Understand which tools are invoked most.

## 7. Monitoring & Alerting

Recommended alerts:
- **High Latency**: `total_latency_ms > 5000`
- **High Error Rate**: `errors / total_requests > 0.05`
- **High Cost**: `estimated_cost_usd > $1.00 per request`
- **Excessive Retries**: `retries > 2`
