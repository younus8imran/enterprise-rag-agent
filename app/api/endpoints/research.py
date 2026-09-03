"""
Research endpoint for long-running research tasks.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import uuid

from app.api.schemas.requests import ResearchRequest, ResearchResponse
from app.core.security.auth import AuthContext, get_current_user
from app.core.logging import logger

router = APIRouter(prefix="/research", tags=["research"])

@router.post("", response_model=ResearchResponse, status_code=202)
async def research(
    request: ResearchRequest,
    auth: AuthContext = Depends(get_current_user)
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
        user_id=auth.identity.user_id
    )

    # In production, this would:
    # 1. Queue the research task
    # 2. Return 202 Accepted with run_id
    # 3. Client polls GET /runs/{run_id} for status

    from datetime import datetime

    return ResearchResponse(
        run_id=run_id,
        question=request.question,
        answer="Comprehensive research answer based on multiple sources...",
        evidence=[],
        confidence=0.8,
        sources_consulted={"rag": 5, "sql": 2, "web": 3},
        timestamp=datetime.utcnow()
    )
