"""
SQL endpoint for natural-language-driven data queries.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from app.core.security.auth import AuthContext, get_current_user
from app.core.security.permissions import AccessControl
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.services.sql.agent import SQLAgent

router = APIRouter(prefix="/sql", tags=["sql"])


class SQLQueryRequest(BaseModel):
    """Request schema for natural-language SQL queries."""
    query: str = Field(..., min_length=1, max_length=2000, description="Natural-language question")
    access_level: Optional[int] = Field(
        None, ge=1, le=3,
        description="Override access level (defaults to user's role-derived level)",
    )


class SQLQueryResponse(BaseModel):
    """Response schema for SQL query execution."""
    success: bool
    sql: str
    row_count: int
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    confidence: float = 0.0
    attempts: int = 0


@router.post("", response_model=SQLQueryResponse)
async def sql_query(
    request: SQLQueryRequest,
    auth: AuthContext = Depends(get_current_user),
):
    """
    Execute a natural-language query against the database.

    RBAC: SQL tool is restricted to admin and manager roles
    (see app.core.security.permissions.AccessControl.validate_tool_permission).

    Pipeline (SQLAgent.query_with_retry):
      inspect_schema → identify_relevant_tables → generate_sql →
      execute_sql (validate + run, 1000-row cap) → on failure: correct_sql (up to 2 retries)
    """
    if not AccessControl.validate_tool_permission(auth.identity, "sql"):
        logger.warning(
            "sql_access_denied",
            user_id=auth.identity.user_id,
            role=auth.identity.role,
        )
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403,
            detail=f"SQL queries require admin or manager role. Your role: {auth.identity.role}",
        )

    logger.info(
        "sql_query_started",
        query=request.query,
        user_id=auth.identity.user_id,
        tenant_id=auth.identity.tenant_id,
    )

    async with AsyncSessionLocal() as db:
        agent = SQLAgent(db_session=db)
        result = await agent.query_with_retry(
            nl_query=request.query,
            tenant_id=auth.identity.tenant_id,
        )

    confidence = 1.0 if result.success else 0.0
    attempts = getattr(agent, "_last_attempts", 0) or 0

    return SQLQueryResponse(
        success=result.success,
        sql=result.sql,
        row_count=result.row_count,
        data=result.data,
        error=result.error,
        confidence=confidence,
        attempts=attempts,
    )
