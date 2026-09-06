from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime


class EvidenceSource(str, Enum):
    """Types of evidence sources to distinguish provenance"""
    INTERNAL_RAG = "internal_rag"  # From enterprise document retrieval
    SQL_QUERY = "sql_query"  # From database queries
    WEB_RESEARCH = "web_research"  # From external web search
    MODEL_INFERENCE = "model_inference"  # LLM reasoning without external evidence


class Citation(BaseModel):
    """Citation with full provenance tracking"""
    source_type: EvidenceSource
    content: str
    url: Optional[HttpUrl] = None
    title: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_markdown(self) -> str:
        """Format citation as markdown for display"""
        if self.source_type == EvidenceSource.INTERNAL_RAG:
            doc_name = self.metadata.get("document_name", "Internal Document")
            return f"[{doc_name}](internal:{self.metadata.get('document_id')})"
        elif self.source_type == EvidenceSource.SQL_QUERY:
            return f"Database Query: {self.metadata.get('query_summary', 'Enterprise Data')}"
        elif self.source_type == EvidenceSource.WEB_RESEARCH:
            return f"[{self.title}]({self.url})"
        elif self.source_type == EvidenceSource.MODEL_INFERENCE:
            return "Model Analysis"
        return "Unknown Source"


class Evidence(BaseModel):
    """
    Source-aware evidence with full citation tracking.
    Clearly distinguishes between different evidence types.
    """
    content: str
    source_type: EvidenceSource
    citation: Citation
    relevance_score: float = Field(ge=0.0, le=1.0, default=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResearchResult(BaseModel):
    """Complete research result with multi-source evidence"""
    query: str
    evidence: List[Evidence]
    answer: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    sources_consulted: Dict[EvidenceSource, int] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_citations_by_type(self, source_type: EvidenceSource) -> List[Citation]:
        """Get all citations of a specific type"""
        return [
            ev.citation
            for ev in self.evidence
            if ev.source_type == source_type
        ]

    def has_sufficient_evidence(self, min_sources: int = 2) -> bool:
        """Check if result has sufficient evidence"""
        return len(self.evidence) >= min_sources

    def format_citations(self) -> str:
        """Format all citations as markdown"""
        citations_by_type = {}
        for ev in self.evidence:
            source_type = ev.source_type.value
            if source_type not in citations_by_type:
                citations_by_type[source_type] = []
            citations_by_type[source_type].append(ev.citation)

        output = []
        for source_type, citations in citations_by_type.items():
            output.append(f"\n### {source_type.replace('_', ' ').title()}")
            for i, citation in enumerate(citations, 1):
                output.append(f"{i}. {citation.to_markdown()}")

        return "\n".join(output)
