import pytest
from app.core.telemetry.collector import TelemetryCollector, request_context

def test_request_lifecycle():
    """Test full request lifecycle tracking"""
    collector = TelemetryCollector()
    
    # 1. Start request
    ctx = collector.start_request(query="Test query", user_id="u123")
    assert ctx.user_id == "u123"
    assert ctx.query == "Test query"
    assert request_context.get() == ctx

    # 2. Track spans
    span = collector.start_span("retrieve_rag", metadata={"tenant": "t1"})
    collector.end_span(span, success=True)
    
    span_err = collector.start_span("retrieve_sql")
    collector.end_span(span_err, success=False, error="Query timeout")

    # 3. Record tool calls and tokens
    collector.record_tool_call("rag")
    collector.record_tool_call("sql")
    collector.record_tokens(prompt_tokens=100, completion_tokens=50)
    collector.record_retry("sql", "Timeout")

    # 4. End request
    collector.end_request(confidence=0.8)
    
    summary = collector.get_summary()
    
    assert summary["user_id"] == "u123"
    assert summary["tool_calls"]["rag"] == 1
    assert summary["tool_calls"]["sql"] == 1
    assert summary["retries"] == 1
    assert summary["total_tokens"] == 150
    assert summary["estimated_cost_usd"] > 0
    assert len(summary["spans"]) == 2
    assert summary["spans"][0]["name"] == "retrieve_rag"
    assert summary["spans"][1]["success"] is False

def test_cost_estimation():
    """Test token-to-cost calculation"""
    collector = TelemetryCollector()
    # Mistral approx: $0.30/1M prompt, $1.00/1M completion
    collector.record_tokens(prompt_tokens=1000, completion_tokens=1000)
    
    # Expected: (1000/1000)*0.0003 + (1000/1000)*0.001 = 0.0003 + 0.001 = 0.0013
    assert abs(collector.estimated_cost_usd - 0.0013) < 1e-6

def test_context_propagation():
    """Test that request context is preserved across calls"""
    collector = TelemetryCollector()
    collector.start_request(query="Propagate me")
    
    # In a real app, this would happen in different nodes
    ctx = request_context.get()
    assert ctx is not None
    assert ctx.query == "Propagate me"
