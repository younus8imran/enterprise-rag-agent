"""
Run status endpoint for tracking long-running tasks.
"""
from fastapi import APIRouter, Depends, HTTPException, Path

from app.api.schemas.requests import RunStatusResponse
from app.core.security.auth import AuthContext, get_current_user
from app.core.logging import logger

router = APIRouter(prefix="/runs", tags=["runs"])

@router.get("/{run_id}", response_model=RunStatusResponse)
async def get_run_status(
    run_id: str = Path(..., description="Run ID from chat or research endpoint"),
    auth: AuthContext = Depends(get_current_user)
):
    """
    Get the status of a long-running task.

    - **run_id**: Unique run identifier

    Returns:
    - **status**: 'running', 'completed', or 'failed'
    - **progress**: Optional progress message
    - **result**: Final result if completed
    - **error**: Error message if failed
    """
    logger.info("get_run_status", run_id=run_id, user_id=auth.identity.user_id)

    # In production, query from a runs table or cache
    # For now, mock a completed run
    return RunStatusResponse(
        run_id=run_id,
        status="completed",
        progress="Task completed successfully",
        result={
            "answer": "Final answer based on research...",
            "confidence": 0.85
        },
        error=None
    )
