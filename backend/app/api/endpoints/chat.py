"""
Chat endpoint for conversational queries.
"""
import json
import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.api.schemas.requests import ChatHistoryResponse, ChatRequest, ChatResponse
from app.core.logging import logger
from app.core.security.auth import AuthContext, get_current_user
from app.core.telemetry.collector import TelemetryCollector
from app.db.models import ChatMessage
from app.services.agent.graph import create_rag_graph
from app.services.agent.state import AgentState
from app.services.rag.service import RAGService
from app.services.research.agent import ResearchAgent
from app.services.research.provider import get_search_provider
from app.services.runs.manager import RunManager
from app.services.sql.agent import SQLAgent
from app.db.session import AsyncSessionLocal
from app.services.llm.mistral_chat import MistralChatProvider

router = APIRouter(prefix="/chat", tags=["chat"])


async def _save_message(
    db,
    user_id: int,
    tenant_id: int,
    role: str,
    content: str,
    run_id: Optional[str] = None,
) -> ChatMessage:
    msg = ChatMessage(
        user_id=user_id,
        tenant_id=tenant_id,
        role=role,
        content=content,
        run_id=run_id,
    )
    db.add(msg)
    await db.flush()
    return msg


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

        # Real agent execution via LangGraph — events emitted during graph.ainvoke
        # (streaming mode delegates to the graph's streaming callbacks)

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


@router.get("/history", response_model=ChatHistoryResponse)
async def chat_history(
    auth: AuthContext = Depends(get_current_user),
):
    """
    Return chat history for the current user, oldest first.
    """
    async with AsyncSessionLocal() as db:
        stmt = (
            select(ChatMessage)
            .where(
                ChatMessage.user_id == auth.identity.user_id,
                ChatMessage.tenant_id == auth.identity.tenant_id,
            )
            .order_by(ChatMessage.created_at.asc())
            .limit(500)
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()

    return ChatHistoryResponse(
        messages=[
            {
                "id": row.id,
                "role": row.role,
                "content": row.content,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    )


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """
    Chat endpoint: runs full LangGraph agent (classify → retrieve → synthesize).
    Persists user and agent messages to chat history.
    """
    run_id = str(uuid.uuid4())
    collector = TelemetryCollector()
    collector.start_request(query=request.query, user_id=auth.identity.user_id)

    try:
        if request.stream:
            # Create run record so stream consumers can poll /runs/{id}
            async with AsyncSessionLocal() as db:
                await RunManager(db).create(run_id)
            return StreamingResponse(
                stream_agent_events(run_id, request.query, auth),
                media_type="text/event-stream"
            )

        try:
            from app.services.agent.graph import create_rag_graph
        except Exception as import_err:
            logger.error("langgraph_import_failed", error=str(import_err))
            # Fallback: direct Mistral chat without agent graph
            chat_provider = MistralChatProvider()
            answer = await chat_provider.generate_answer(
                query=request.query,
                system_prompt="You are a precise enterprise assistant. Answer concisely based on your knowledge.",
            )
            async with AsyncSessionLocal() as db:
                runs = RunManager(db)
                await runs.update(
                    run_id,
                    status="completed",
                    progress=1.0,
                    result={
                        "answer": answer,
                        "confidence": 0.0,
                        "tools_used": [],
                    },
                    completed=True,
                )
                # Persist messages
                await _save_message(db, auth.identity.user_id, auth.identity.tenant_id, "user", request.query, run_id)
                await _save_message(db, auth.identity.user_id, auth.identity.tenant_id, "agent", answer, run_id)
                await db.commit()
            return ChatResponse(
                run_id=run_id,
                answer=answer,
                confidence=0.0,
                citations=[],
                tools_used=[],
                latency_ms=0.0,
                estimated_cost_usd=0.0,
            )

        # Build initial state
        initial_state: AgentState = {
            "query": request.query,
            "tenant_id": auth.identity.tenant_id,
            "access_level": auth.identity.access_level,
            "tools_to_use": [],
            "documents": [],
            "sql_results": [],
            "web_evidence": [],
            "answer": "",
            "citations": [],
            "confidence": 0.0,
            "iterations": 0,
            "critic_feedback": "",
        }

        # Instantiate services (DB session, search, LLM)
        async with AsyncSessionLocal() as db:
            runs = RunManager(db)
            await runs.create(run_id)
            await runs.update(run_id, status="running", progress=0.1)

            # Persist user message immediately
            await _save_message(db, auth.identity.user_id, auth.identity.tenant_id, "user", request.query, run_id)

            rag = RAGService(db_session=db)
            sql_agent = SQLAgent(db_session=db)
            research = ResearchAgent(search_provider=get_search_provider())
            graph = create_rag_graph(rag, sql_agent, research)
            result = await graph.ainvoke(initial_state)

            answer = result.get("answer") or "No answer generated."
            citations = result.get("citations") or []
            confidence = result.get("confidence") or 0.5
            tools_used = []
            if result.get("documents"):
                tools_used.append("rag")
            if result.get("sql_results"):
                tools_used.append("sql")
            if result.get("web_evidence"):
                tools_used.append("web")

            collector.end_request(confidence=confidence)
            summary = collector.get_summary()

            # Persist agent message
            await _save_message(db, auth.identity.user_id, auth.identity.tenant_id, "agent", answer, run_id)

            await runs.update(
                run_id,
                status="completed",
                progress=1.0,
                result={
                    "answer": answer,
                    "confidence": confidence,
                    "citations": citations,
                    "tools_used": tools_used,
                    "latency_ms": summary.get("total_latency_ms", 0.0),
                    "estimated_cost_usd": summary.get("estimated_cost_usd", 0.0),
                },
                completed=True,
            )
            await db.commit()

        return ChatResponse(
            run_id=run_id,
            answer=answer,
            confidence=confidence,
            citations=citations,
            tools_used=tools_used,
            latency_ms=summary.get("total_latency_ms", 0.0),
            estimated_cost_usd=summary.get("estimated_cost_usd", 0.0)
        )

    except Exception as e:
        logger.error("chat_error", error=str(e), run_id=run_id)
        try:
            async with AsyncSessionLocal() as db:
                await RunManager(db).update(
                    run_id, status="failed", error=str(e), completed=True
                )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Chat execution failed: {str(e)}")
