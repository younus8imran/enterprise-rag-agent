import pytest
from app.services.research.evidence import (
    Evidence,
    EvidenceSource,
    Citation,
    ResearchResult,
)
from datetime import datetime


def test_evidence_source_types():
    """Test that all evidence source types are distinct"""
    sources = [
        EvidenceSource.INTERNAL_RAG,
        EvidenceSource.SQL_QUERY,
        EvidenceSource.WEB_RESEARCH,
        EvidenceSource.MODEL_INFERENCE,
    ]

    assert len(sources) == len(set(sources))


def test_citation_to_markdown_web():
    """Test web research citation formatting"""
    citation = Citation(
        source_type=EvidenceSource.WEB_RESEARCH,
        content="AI is transforming industries.",
        url="https://example.com/ai",
        title="What is AI?",
    )

    markdown = citation.to_markdown()

    assert markdown == "[What is AI?](https://example.com/ai)"


def test_citation_to_markdown_internal():
    """Test internal RAG citation formatting"""
    citation = Citation(
        source_type=EvidenceSource.INTERNAL_RAG,
        content="Company policy on AI usage.",
        metadata={"document_name": "AI Policy", "document_id": 123},
    )

    markdown = citation.to_markdown()

    assert "AI Policy" in markdown
    assert "internal:" in markdown


def test_citation_to_markdown_sql():
    """Test SQL query citation formatting"""
    citation = Citation(
        source_type=EvidenceSource.SQL_QUERY,
        content="Revenue data from Q1 2024.",
        metadata={"query_summary": "Q1 2024 Revenue"},
    )

    markdown = citation.to_markdown()

    assert "Database Query" in markdown
    assert "Q1 2024 Revenue" in markdown


def test_citation_to_markdown_model():
    """Test model inference citation formatting"""
    citation = Citation(
        source_type=EvidenceSource.MODEL_INFERENCE,
        content="Based on the available context...",
    )

    markdown = citation.to_markdown()

    assert markdown == "Model Analysis"


def test_evidence_creation():
    """Test evidence object creation"""
    citation = Citation(
        source_type=EvidenceSource.WEB_RESEARCH,
        content="Test content",
        url="https://example.com",
        title="Test",
    )

    evidence = Evidence(
        content="Test content",
        source_type=EvidenceSource.WEB_RESEARCH,
        citation=citation,
        relevance_score=0.85,
    )

    assert evidence.content == "Test content"
    assert evidence.source_type == EvidenceSource.WEB_RESEARCH
    assert evidence.relevance_score == 0.85
    assert evidence.citation == citation


def test_research_result_has_sufficient_evidence():
    """Test sufficient evidence check"""
    citation = Citation(
        source_type=EvidenceSource.WEB_RESEARCH,
        content="Test",
        url="https://example.com",
        title="Test",
    )

    evidence1 = Evidence(
        content="Evidence 1",
        source_type=EvidenceSource.WEB_RESEARCH,
        citation=citation,
    )

    evidence2 = Evidence(
        content="Evidence 2",
        source_type=EvidenceSource.WEB_RESEARCH,
        citation=citation,
    )

    result = ResearchResult(query="test", evidence=[evidence1, evidence2])

    assert result.has_sufficient_evidence(min_sources=2)
    assert not result.has_sufficient_evidence(min_sources=3)


def test_research_result_get_citations_by_type():
    """Test filtering citations by type"""
    web_citation = Citation(
        source_type=EvidenceSource.WEB_RESEARCH,
        content="Web content",
        url="https://example.com",
        title="Web",
    )

    sql_citation = Citation(
        source_type=EvidenceSource.SQL_QUERY,
        content="SQL data",
        metadata={"query_summary": "Revenue"},
    )

    evidence = [
        Evidence(
            content="Web",
            source_type=EvidenceSource.WEB_RESEARCH,
            citation=web_citation,
        ),
        Evidence(
            content="SQL",
            source_type=EvidenceSource.SQL_QUERY,
            citation=sql_citation,
        ),
        Evidence(
            content="Web2",
            source_type=EvidenceSource.WEB_RESEARCH,
            citation=web_citation,
        ),
    ]

    result = ResearchResult(query="test", evidence=evidence)

    web_cites = result.get_citations_by_type(EvidenceSource.WEB_RESEARCH)
    sql_cites = result.get_citations_by_type(EvidenceSource.SQL_QUERY)

    assert len(web_cites) == 2
    assert len(sql_cites) == 1


def test_research_result_format_citations():
    """Test formatting all citations"""
    web_citation = Citation(
        source_type=EvidenceSource.WEB_RESEARCH,
        content="Web content",
        url="https://example.com",
        title="Example",
    )

    internal_citation = Citation(
        source_type=EvidenceSource.INTERNAL_RAG,
        content="Internal doc",
        metadata={"document_name": "Policy", "document_id": 1},
    )

    evidence = [
        Evidence(
            content="Web",
            source_type=EvidenceSource.WEB_RESEARCH,
            citation=web_citation,
        ),
        Evidence(
            content="Internal",
            source_type=EvidenceSource.INTERNAL_RAG,
            citation=internal_citation,
        ),
    ]

    result = ResearchResult(query="test", evidence=evidence)

    formatted = result.format_citations()

    assert "Web Research" in formatted
    assert "Internal Rag" in formatted
    assert "[Example](https://example.com/)" in formatted
    assert "Policy" in formatted


def test_evidence_relevance_score_bounds():
    """Test that relevance scores are bounded [0, 1]"""
    citation = Citation(
        source_type=EvidenceSource.WEB_RESEARCH,
        content="Test",
        url="https://example.com",
        title="Test",
    )

    # Valid scores
    Evidence(
        content="Test",
        source_type=EvidenceSource.WEB_RESEARCH,
        citation=citation,
        relevance_score=0.0,
    )

    Evidence(
        content="Test",
        source_type=EvidenceSource.WEB_RESEARCH,
        citation=citation,
        relevance_score=1.0,
    )

    # Invalid scores should raise validation error
    with pytest.raises(Exception):
        Evidence(
            content="Test",
            source_type=EvidenceSource.WEB_RESEARCH,
            citation=citation,
            relevance_score=1.5,
        )

    with pytest.raises(Exception):
        Evidence(
            content="Test",
            source_type=EvidenceSource.WEB_RESEARCH,
            citation=citation,
            relevance_score=-0.1,
        )


def test_citation_metadata():
    """Test citation metadata storage"""
    citation = Citation(
        source_type=EvidenceSource.WEB_RESEARCH,
        content="Content",
        url="https://example.com",
        title="Title",
        metadata={"domain": "example.com", "rank": 1},
    )

    assert citation.metadata["domain"] == "example.com"
    assert citation.metadata["rank"] == 1


def test_research_result_sources_consulted():
    """Test tracking of sources consulted"""
    result = ResearchResult(
        query="test",
        evidence=[],
        sources_consulted={
            EvidenceSource.WEB_RESEARCH: 5,
            EvidenceSource.INTERNAL_RAG: 3,
        },
    )

    assert result.sources_consulted[EvidenceSource.WEB_RESEARCH] == 5
    assert result.sources_consulted[EvidenceSource.INTERNAL_RAG] == 3
