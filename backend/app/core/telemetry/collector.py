"""
Telemetry and observability for the Enterprise Intelligence Agent.
Tracks request lifecycle, performance metrics, and costs.
"""
import time
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextvars import ContextVar
from pydantic import BaseModel, Field
from app.core.logging import logger

# Context variable for request ID propagation
request_context: ContextVar[Optional["RequestContext"]] = ContextVar("request_context", default=None)

class RequestContext(BaseModel):
    """Context object propagated through the request lifecycle"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[int] = None
    tenant_id: Optional[int] = None
    query: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SpanMetrics(BaseModel):
    """Metrics for a single operation span"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TelemetryCollector:
    """
    Collects telemetry data for observability.
    Compatible with OpenTelemetry/LangSmith tracing.
    """

    def __init__(self):
        self.spans: List[SpanMetrics] = []
        self.request_start_time: Optional[float] = None
        self.request_end_time: Optional[float] = None

        # Counters
        self.tool_calls: Dict[str, int] = {}
        self.retries: int = 0
        self.errors: int = 0

        # Cost tracking (estimated)
        self.total_tokens: int = 0
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.estimated_cost_usd: float = 0.0

    def start_request(self, query: str, user_id: Optional[int] = None):
        """Start tracking a new request"""
        ctx = RequestContext(
            query=query,
            user_id=user_id
        )
        request_context.set(ctx)
        self.request_start_time = time.time()

        logger.info(
            "request_started",
            request_id=ctx.request_id,
            user_id=user_id,
            query=query[:100]  # Truncate for safety
        )

        return ctx

    def start_span(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> SpanMetrics:
        """Start tracking an operation span"""
        span = SpanMetrics(
            name=name,
            start_time=time.time(),
            metadata=metadata or {}
        )

        ctx = request_context.get()
        if ctx:
            logger.info(
                "span_started",
                request_id=ctx.request_id,
                span=name,
                **span.metadata
            )

        return span

    def end_span(self, span: SpanMetrics, success: bool = True, error: Optional[str] = None):
        """End tracking an operation span"""
        span.end_time = time.time()
        span.duration_ms = (span.end_time - span.start_time) * 1000
        span.success = success
        span.error = error

        self.spans.append(span)

        ctx = request_context.get()
        if ctx:
            logger.info(
                "span_completed",
                request_id=ctx.request_id,
                span=span.name,
                duration_ms=round(span.duration_ms, 2),
                success=success,
                error=error
            )

        if not success:
            self.errors += 1

    def record_tool_call(self, tool_name: str):
        """Record a tool invocation"""
        self.tool_calls[tool_name] = self.tool_calls.get(tool_name, 0) + 1

        ctx = request_context.get()
        if ctx:
            logger.info(
                "tool_invoked",
                request_id=ctx.request_id,
                tool=tool_name,
                count=self.tool_calls[tool_name]
            )

    def record_retry(self, component: str, reason: str):
        """Record a retry attempt"""
        self.retries += 1

        ctx = request_context.get()
        if ctx:
            logger.warning(
                "retry_attempt",
                request_id=ctx.request_id,
                component=component,
                reason=reason,
                retry_count=self.retries
            )

    def record_tokens(self, prompt_tokens: int, completion_tokens: int):
        """Record token usage for cost estimation"""
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens = self.prompt_tokens + self.completion_tokens

        # Cost estimation for Mistral (approximate rates)
        # Adjust these based on actual Mistral pricing
        cost_per_1k_prompt = 0.0003  # $0.30 per 1M tokens
        cost_per_1k_completion = 0.001  # $1.00 per 1M tokens

        self.estimated_cost_usd = (
            (self.prompt_tokens / 1000) * cost_per_1k_prompt +
            (self.completion_tokens / 1000) * cost_per_1k_completion
        )

    def end_request(self, confidence: float = 0.0):
        """Finalize request tracking and emit summary telemetry"""
        self.request_end_time = time.time()

        ctx = request_context.get()
        if not ctx:
            return

        total_latency_ms = (self.request_end_time - self.request_start_time) * 1000

        # Compute per-component latencies
        retrieval_latency = sum(
            s.duration_ms for s in self.spans
            if s.name in ["retrieve_rag", "hybrid_search", "rerank"] and s.duration_ms
        )
        sql_latency = sum(
            s.duration_ms for s in self.spans
            if s.name in ["retrieve_sql", "execute_sql"] and s.duration_ms
        )
        web_latency = sum(
            s.duration_ms for s in self.spans
            if s.name in ["retrieve_web", "research"] and s.duration_ms
        )

        # Emit final telemetry (safe, no chain-of-thought)
        logger.info(
            "request_completed",
            request_id=ctx.request_id,
            user_id=ctx.user_id,
            total_latency_ms=round(total_latency_ms, 2),
            retrieval_latency_ms=round(retrieval_latency, 2),
            sql_latency_ms=round(sql_latency, 2),
            web_latency_ms=round(web_latency, 2),
            tool_calls=self.tool_calls,
            retries=self.retries,
            errors=self.errors,
            confidence=confidence,
            total_tokens=self.total_tokens,
            estimated_cost_usd=round(self.estimated_cost_usd, 6)
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of telemetry for this request"""
        ctx = request_context.get()

        if not ctx or not self.request_end_time:
            return {}

        total_latency_ms = (self.request_end_time - self.request_start_time) * 1000

        return {
            "request_id": ctx.request_id,
            "user_id": ctx.user_id,
            "query": ctx.query[:100],
            "timestamp": ctx.timestamp.isoformat(),
            "total_latency_ms": round(total_latency_ms, 2),
            "tool_calls": self.tool_calls,
            "retries": self.retries,
            "errors": self.errors,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "spans": [
                {
                    "name": s.name,
                    "duration_ms": round(s.duration_ms, 2) if s.duration_ms else None,
                    "success": s.success
                }
                for s in self.spans
            ]
        }
