"""
Pydantic schemas for API request/response models.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# ===== Chat Endpoint =====
class ChatRequest(BaseModel):
    """Request schema for chat endpoint"""
    query: str = Field(..., min_length=1, max_length=2000, description="User question")
    context: Optional[str] = Field(None, description="Optional additional context")
    stream: bool = Field(False, description="Whether to stream the response")

class ChatResponse(BaseModel):
    """Response schema for chat endpoint"""
    run_id: str
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    citations: List[Any]
    tools_used: List[str]
    latency_ms: float
    estimated_cost_usd: float

# ===== Research Endpoint =====
class ResearchRequest(BaseModel):
    """Request schema for research endpoint"""
    question: str = Field(..., min_length=1, max_length=2000)
    tools: Optional[List[str]] = Field(None, description="Specific tools to use: 'rag', 'sql', 'web'")
    stream: bool = Field(True, description="Stream status updates")

class ResearchResponse(BaseModel):
    """Response schema for research endpoint"""
    run_id: str
    question: str
    answer: str
    evidence: List[Dict[str, Any]]
    confidence: float
    sources_consulted: Dict[str, int]
    timestamp: datetime

# ===== Document Ingestion =====
class DocumentIngestRequest(BaseModel):
    """Request schema for document ingestion (file_path-based, for internal use)."""
    file_path: str = Field(..., description="Path to document file")
    tenant_id: str
    access_level: int = Field(1, ge=1, le=3, description="1=Basic, 2=Confidential, 3=Top Secret")
    metadata: Optional[Dict[str, Any]] = None


class DocumentIngestMetadata(BaseModel):
    """Metadata fields that accompany a file upload during ingestion."""
    tenant_id: str
    access_level: int = Field(1, ge=1, le=3, description="1=Basic, 2=Confidential, 3=Top Secret")
    metadata: Optional[Dict[str, Any]] = None

class DocumentIngestResponse(BaseModel):
    """Response schema for document ingestion"""
    document_id: int
    chunks_created: int
    status: str

class DocumentListResponse(BaseModel):
    """Response schema for listing documents"""
    documents: List[Dict[str, Any]]
    total: int

# ===== Run Status =====
class RunStatusResponse(BaseModel):
    """Response schema for run status"""
    run_id: str
    status: str = Field(..., description="'running', 'completed', 'failed'")
    progress: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# ===== Streaming Events =====
class StreamEvent(BaseModel):
    """Schema for streaming status events"""
    event: str = Field(..., description="Event type: 'status', 'result', 'error'")
    data: Dict[str, Any]

# ===== Error Responses =====
class ErrorResponse(BaseModel):
    """Standard error response schema"""
    detail: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
