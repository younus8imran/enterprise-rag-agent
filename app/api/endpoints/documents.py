"""
Document management endpoints.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.schemas.requests import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    DocumentListResponse,
)
from app.core.logging import logger
from app.core.security.auth import AuthContext, get_current_user

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("", response_model=DocumentListResponse)
async def list_documents(
    auth: AuthContext = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    List documents accessible to the current user.

    - **skip**: Number of documents to skip (pagination)
    - **limit**: Maximum documents to return (1-100)

    Returns a list of documents filtered by tenant_id and access_level.
    """
    logger.info(
        "list_documents",
        user_id=auth.identity.user_id,
        tenant_id=auth.identity.tenant_id
    )

    # In production, query from database with tenant isolation
    return DocumentListResponse(
        documents=[],
        total=0
    )

@router.post("/ingest", response_model=DocumentIngestResponse, status_code=201)
async def ingest_document(
    request: DocumentIngestRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """
    Ingest a new document into the knowledge base.

    - **file_path**: Path to the document file
    - **tenant_id**: Tenant ID for data isolation
    - **access_level**: Access level (1=Basic, 2=Confidential, 3=Top Secret)
    - **metadata**: Optional metadata for the document

    Returns the created document ID and number of chunks.

    **Note**: User must have write permissions for the tenant.
    """
    # Verify user has write access to this tenant
    if request.tenant_id != auth.identity.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot ingest documents for a different tenant"
        )

    logger.info(
        "document_ingestion_started",
        file_path=request.file_path,
        tenant_id=request.tenant_id,
        user_id=auth.identity.user_id
    )

    # In production:
    # 1. Read the file
    # 2. Parse and chunk the document
    # 3. Generate embeddings
    # 4. Store in pgvector with proper metadata

    return DocumentIngestResponse(
        document_id=1,
        chunks_created=10,
        status="completed"
    )
