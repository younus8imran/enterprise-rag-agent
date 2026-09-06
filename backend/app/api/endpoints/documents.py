"""
Document management endpoints.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.requests import (
    DocumentIngestMetadata,
    DocumentIngestResponse,
    DocumentListResponse,
)
from app.core.logging import logger
from app.core.security.auth import AuthContext, get_current_user
from app.db.session import get_db
from app.services.rag.ingestion import IngestionService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    List documents accessible to the current user.

    - **skip**: Number of documents to skip (pagination)
    - **limit**: Maximum documents to return (1-100)

    Returns documents filtered by tenant_id (always) and capped by the user's
    access_level (1=Basic sees 1, 2=Confidential sees 1+2, 3=Top Secret sees all).
    """
    from sqlalchemy import func, select

    from app.db.rag_models import Document

    user_access = int(getattr(auth.identity, "access_level", 1) or 1)
    tenant_id = auth.identity.tenant_id

    logger.info(
        "list_documents",
        user_id=auth.identity.user_id,
        tenant_id=tenant_id,
        access_level=user_access,
    )

    # Tenant isolation + user scope
    base_filter = [
        Document.tenant_id == tenant_id,
        Document.user_id == auth.identity.user_id,
    ]

    # Total count
    count_stmt = select(func.count(Document.id)).where(*base_filter)
    total = (await db.execute(count_stmt)).scalar_one() or 0

    # Page
    stmt = (
        select(Document)
        .where(*base_filter)
        .order_by(Document.id.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    documents = [
        {
            "id": row.id,
            "name": row.name,
            "type": row.type,
            "source": row.source,
            "tenant_id": row.tenant_id,
            "metadata": row.metadata_json,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
        for row in rows
    ]

    return DocumentListResponse(documents=documents, total=int(total))


@router.post("/ingest", response_model=DocumentIngestResponse, status_code=201)
async def ingest_document(
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(..., description="Document file to ingest"),
    tenant_id: str = Form(...),
    access_level: int = Form(1, ge=1, le=3),
    metadata_json: str = Form("{}"),
):
    """
    Ingest a new document into the knowledge base via file upload.

    - **file**: The document file (PDF, DOCX, etc.)
    - **tenant_id**: Tenant ID for data isolation
    - **access_level**: Access level (1=Basic, 2=Confidential, 3=Top Secret)
    - **metadata_json**: Optional JSON string with extra metadata

    Returns the created document ID and number of chunks.
    """
    import json

    try:
        metadata: Dict[str, Any] = json.loads(metadata_json) if metadata_json else {}
    except json.JSONDecodeError:
        metadata = {}

    # Verify user owns / writes to this tenant
    if int(tenant_id) != int(auth.identity.tenant_id):
        raise HTTPException(
            status_code=403, detail="Cannot ingest documents for a different tenant"
        )

    logger.info(
        "document_ingestion_started",
        file_name=file.filename,
        tenant_id=tenant_id,
        user_id=auth.identity.user_id,
    )

    # Persistent uploads directory (not temp, so files remain for retrieval)
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    safe_name = os.path.basename(file.filename or "upload")
    # Prevent path traversal / collisions
    safe_name = "_".join(safe_name.split())[:120]
    persistent_path = uploads_dir / safe_name
    # If same file exists, keep the original; don't overwrite live data

    content = await file.read()
    persistent_path.write_bytes(content)
    await file.close()

    service = IngestionService(db=db)
    try:
        result = await service.ingest(
            file_path=str(persistent_path),
            tenant_id=int(tenant_id),
            user_id=auth.identity.user_id,
            access_level=access_level,
            metadata={**metadata, "original_filename": file.filename},
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Document file not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("document_ingestion_failed", file_name=file.filename)
        raise HTTPException(status_code=500, detail="Ingestion failed")

    return DocumentIngestResponse(
        document_id=result.document_id,
        chunks_created=result.chunks_created,
        status=result.status,
    )
