"""
Run status endpoint for tracking long-running tasks.
"""
from fastapi import APIRouter, Depends, HTTPException, Path

from app.api.schemas.requests import RunStatusResponse
from app.core.security.auth import AuthContext, get_current_user
from app.core.logging import logger
from app.services.runs.manager import RunManager
from app.db.session import AsyncSessionLocal

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

    async with AsyncSessionLocal() as db:
        run = await RunManager(db).get(run_id)

    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    # Convert progress float to human-readable progress message
    progress_msg = None
    if run.status == "running":
        progress_msg = f"Processing... {int(run.progress * 100)}%"

    return RunStatusResponse(
        run_id=run.id,
        status=run.status,
        progress=progress_msg,
        result=run.result,
        error=run.error
    )
