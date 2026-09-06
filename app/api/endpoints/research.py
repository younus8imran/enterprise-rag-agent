"""
Research endpoint for long-running research tasks.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
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


@router.post("", response_model=ResearchResponse, status_code=202)
async def research(
    request: ResearchRequest,
    auth: AuthContext = Depends(get_current_user),
):
    """
    Research endpoint for complex, multi-tool research tasks.

    - **question**: Research question (1-2000 characters)
    - **tools**: Optional list of specific tools to use
    - **stream**: Whether to stream status updates (default: true)

    Returns comprehensive research results with evidence from multiple sources.
    """
    run_id = str(uuid.uuid4())

    logger.info(
        "research_started",
        run_id=run_id,
        question=request.question,
        user_id=auth.identity.user_id,
    )

    async with AsyncSessionLocal() as db:
        runs = RunManager(db)
        await runs.create(run_id)
        await runs.update(run_id, status="running", progress=0.1)

        # Build evidence from web research
        search_provider = get_search_provider()
        research_agent = ResearchAgent(search_provider=search_provider)
        result = await research_agent.research(question=request.question)

        # Synthesize an answer from evidence using Mistral
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

        # Convert EvidenceSource enum keys to strings for the response
        sources_str: dict[str, int] = {
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
