"""
Research endpoint for long-running research tasks.
"""
import json
import uuid
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.schemas.requests import ResearchRequest, ResearchResponse
from app.core.logging import logger
from app.core.security.auth import AuthContext, get_current_user
from app.services.llm.mistral_chat import MistralChatProvider
from app.services.research.agent import ResearchAgent
from app.services.research.evidence import EvidenceSource
from app.services.research.provider import get_search_provider
from app.services.runs.manager import RunManager
from app.db.session import AsyncSessionLocal

router = APIRouter(prefix="/research", tags=["research"])


async def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def research_generator(
    run_id: str,
    question: str,
    tools: list[str] | None,
) -> AsyncGenerator[str, None]:
    """
    Runs the full research pipeline and yields SSE chunks.
    Yields status events as work progresses, then a 'result' event with
    the final response, then 'done'.
    """
    async with AsyncSessionLocal() as db:
        runs = RunManager(db)
        await runs.create(run_id)
        await runs.update(run_id, status="running", progress=0.1)
        yield await _sse_event("status", {"status": "running", "progress": 0.1, "run_id": run_id})

        # Run research with requested tools
        search_provider = get_search_provider()
        research_agent = ResearchAgent(search_provider=search_provider)
        yield await _sse_event("status", {"status": "researching", "progress": 0.3, "message": f"Using tools: {tools or ['web']}"})
        result = await research_agent.research(question=question, tools=tools)
        yield await _sse_event("status", {"status": "synthesizing", "progress": 0.7, "message": "Synthesizing answer..."})

        # Synthesize answer
        evidence_text = "\n\n".join(
            f"[{i+1}] {e.content}" for i, e in enumerate(result.evidence)
        ) if result.evidence else None
        chat = MistralChatProvider()
        answer = await chat.generate_answer(
            query=question,
            context=evidence_text,
            system_prompt=(
                "You are a precise research assistant. Synthesize a clear, concise answer "
                "from the provided evidence. If the evidence is insufficient, say so. "
                "Cite sources inline as [1], [2], etc."
            ),
        )

        sources_str = {
            (k.value if isinstance(k, EvidenceSource) else str(k)): v
            for k, v in result.sources_consulted.items()
        }
        final_result = {
            "run_id": run_id,
            "question": question,
            "answer": answer,
            "confidence": result.confidence,
            "evidence": [e.model_dump(mode="json") for e in result.evidence],
            "sources_consulted": sources_str,
            "timestamp": (result.timestamp or datetime.utcnow()).isoformat(),
        }

        await runs.update(
            run_id,
            status="completed",
            progress=1.0,
            result=final_result,
            completed=True,
        )

        yield await _sse_event("result", final_result)
        yield await _sse_event("done", {})


@router.post("", response_model=ResearchResponse, status_code=202)
async def research(
    request: ResearchRequest,
    auth: AuthContext = Depends(get_current_user),
):
    """
    Research endpoint for complex, multi-tool research tasks.

    - **question**: Research question (1-2000 characters)
    - **tools**: Optional list of specific tools to use: 'rag', 'sql', 'web'
    - **stream**: Whether to stream status updates via SSE (default: true)

    Returns comprehensive research results with evidence from multiple sources.
    """
    run_id = str(uuid.uuid4())

    logger.info(
        "research_started",
        run_id=run_id,
        question=request.question,
        tools=request.tools,
        user_id=auth.identity.user_id,
        stream=request.stream,
    )

    if request.stream:
        return StreamingResponse(
            research_generator(run_id, request.question, request.tools),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    # Non-streaming path
    async with AsyncSessionLocal() as db:
        runs = RunManager(db)
        await runs.create(run_id)
        await runs.update(run_id, status="running", progress=0.1)

        search_provider = get_search_provider()
        research_agent = ResearchAgent(search_provider=search_provider)
        result = await research_agent.research(question=request.question, tools=request.tools)

        evidence_text = "\n\n".join(
            f"[{i+1}] {e.content}" for i, e in enumerate(result.evidence)
        ) if result.evidence else None
        chat = MistralChatProvider()
        answer = await chat.generate_answer(
            query=request.question,
            context=evidence_text,
            system_prompt=(
                "You are a precise research assistant. Synthesize a clear, concise answer "
                "from the provided evidence. If the evidence is insufficient, say so. "
                "Cite sources inline as [1], [2], etc."
            ),
        )

        sources_str = {
            (k.value if isinstance(k, EvidenceSource) else str(k)): v
            for k, v in result.sources_consulted.items()
        }

        await runs.update(
            run_id,
            status="completed",
            progress=1.0,
            result={
                "answer": answer,
                "confidence": result.confidence,
                "evidence": [e.model_dump(mode="json") for e in result.evidence],
                "sources_consulted": sources_str,
            },
            completed=True,
        )

    return ResearchResponse(
        run_id=run_id,
        question=request.question,
        answer=answer,
        evidence=[e.model_dump(mode="json") for e in result.evidence],
        confidence=result.confidence,
        sources_consulted=sources_str,
        timestamp=result.timestamp or datetime.utcnow(),
    )
