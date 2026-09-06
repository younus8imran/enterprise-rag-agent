"""
Run manager: persists run status to the database.
"""
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Run


class RunManager:
    """Manages run status records in the database."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create(self, run_id: str, user_id: int = None, tenant_id: int = None) -> Run:
        """Create a new run record with status 'running'."""
        run = Run(
            id=run_id, status="running", progress=0.0,
            result=None, error=None,
            user_id=user_id, tenant_id=tenant_id,
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def get(self, run_id: str) -> Optional[Run]:
        """Fetch a run record by ID."""
        result = await self.db.execute(select(Run).where(Run.id == run_id))
        return result.scalar_one_or_none()

    async def update(
        self,
        run_id: str,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        completed: bool = False,
    ) -> Optional[Run]:
        """Update an existing run record."""
        run = await self.get(run_id)
        if not run:
            return None

        if status is not None:
            run.status = status
        if progress is not None:
            run.progress = progress
        if result is not None:
            run.result = result
        if error is not None:
            run.error = error
        if completed:
            from datetime import datetime
            run.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(run)
        return run
