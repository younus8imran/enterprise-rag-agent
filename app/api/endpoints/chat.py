"""
Chat endpoint for conversational queries.
"""
import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.schemas.requests import ChatRequest, ChatResponse, StreamEvent
from app.core.logging import logger
from app.core.security.auth import AuthContext, get_current_user
from app.core.telemetry.collector import TelemetryCollector
from app.services.agent.graph import create_rag_graph
from app.services.rag.service import RAGService
from app.services.research.agent import ResearchAgent
from app.services.research.provider import MockSearchProvider
from app.services.sql.agent import SQLAgent

router = APIRouter(prefix="/chat", tags=["chat"])

async def stream_agent_events(
    run_id: str,
    query: str,
    auth: AuthContext
) -> AsyncGenerator[str, None]:
    """
    Stream safe status events during agent execution.
    Does NOT expose chain-of-thought or internal reasoning.
    """
    try:
        # Emit planning event
        yield json.dumps({
            "event": "status",
            "data": {"run_id": run_id, "status": "Planning", "progress": 0.1}
        }) + "\n"

        # Mock agent execution with status updates
        # In production, this would hook into the actual LangGraph execution

        yield json.dumps({
            "event": "status",
            "data": {"run_id": run_id, "status": "Searching internal documents", "progress": 0.3}
        }) + "\n"

        yield json.dumps({
            "event": "status",
            "data": {"run_id": run_id, "status": "Running SQL analysis", "progress": 0.5}
        }) + "\n"

        yield json.dumps({
            "event": "status",
            "data": {"run_id": run_id, "status": "Researching external sources", "progress": 0.7}
        }) + "\n"

        yield json.dumps({
            "event": "status",
            "data": {"run_id": run_id, "status": "Evaluating evidence", "progress": 0.85}
        }) + "\n"

        yield json.dumps({
            "event": "status",
            "data": {"run_id": run_id, "status": "Generating answer", "progress": 0.95}
        }) + "\n"

        # Final result
        result = {
            "run_id": run_id,
            "answer": "Based on the evidence gathered, the answer is...",
            "confidence": 0.85,
            "citations": ["doc_123", "sql_result"],
            "tools_used": ["rag", "sql"],
            "latency_ms": 1234.56,
            "estimated_cost_usd": 0.0012
        }

        yield json.dumps({
            "event": "result",
            "data": result
        }) + "\n"

    except Exception as e:
        logger.error("streaming_error", error=str(e))
        yield json.dumps({
            "event": "error",
            "data": {"error": str(e)}
        }) + "\n"

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """
    Chat endpoint for conversational queries.

    - **query**: User's question (1-2000 characters)
    - **context**: Optional additional context
    - **stream**: Whether to stream status updates

    Returns a complete answer with citations, tools used, and performance metrics.
    """
    run_id = str(uuid.uuid4())

    # Initialize telemetry
    collector = TelemetryCollector()
    collector.start_request(query=request.query, user_id=auth.identity.user_id)

    try:
        # If streaming, return SSE stream
        if request.stream:
            return StreamingResponse(
                stream_agent_events(run_id, request.query, auth),
                media_type="text/event-stream"
            )

        # Non-streaming: execute and return
        # Mock execution for now
        collector.record_tool_call("rag")
        collector.record_tokens(prompt_tokens=100, completion_tokens=50)
        collector.end_request(confidence=0.85)

        summary = collector.get_summary()

        return ChatResponse(
            run_id=run_id,
            answer="Based on the retrieved evidence, the answer is...",
            confidence=0.85,
            citations=["doc_123", "sql_result"],
            tools_used=["rag", "sql"],
            latency_ms=summary.get("total_latency_ms", 0.0),
            estimated_cost_usd=summary.get("estimated_cost_usd", 0.0)
        )

    except Exception as e:
        logger.error("chat_error", error=str(e), run_id=run_id)
        raise HTTPException(status_code=500, detail=f"Chat execution failed: {str(e)}")
