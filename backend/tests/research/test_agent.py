import pytest
from app.services.research.provider import MockSearchProvider, SearchResponse
from app.services.research.agent import ResearchAgent
from app.services.research.evidence import EvidenceSource


@pytest.mark.asyncio
async def test_successful_research():
    """Test complete research flow with results"""
    provider = MockSearchProvider()
    agent = ResearchAgent(provider)

    result = await agent.research("What is artificial intelligence?")

    assert result.query == "What is artificial intelligence?"
    assert len(result.evidence) > 0
    assert result.confidence > 0.0
    assert EvidenceSource.WEB_RESEARCH in result.sources_consulted
    assert result.sources_consulted[EvidenceSource.WEB_RESEARCH] > 0

    # Check evidence has proper citations
    for ev in result.evidence:
        assert ev.source_type == EvidenceSource.WEB_RESEARCH
        assert ev.citation.url is not None
        assert ev.citation.title is not None
        assert ev.content is not None


@pytest.mark.asyncio
async def test_complex_question_multiple_queries():
    """Test that complex questions generate multiple queries"""
    provider = MockSearchProvider()
    agent = ResearchAgent(provider)

    queries = await agent.generate_queries(
        "Compare artificial intelligence vs machine learning"
    )

    # Complex question should generate multiple queries
    assert len(queries) > 1
    assert any(q.intent == "primary_question" for q in queries)


@pytest.mark.asyncio
async def test_simple_question_single_query():
    """Test that simple questions generate a single query"""
    provider = MockSearchProvider()
    agent = ResearchAgent(provider)

    queries = await agent.generate_queries("What is AI?")

    # Simple question should generate one query
    assert len(queries) == 1
    assert queries[0].intent == "direct_answer"


@pytest.mark.asyncio
async def test_duplicate_source_handling():
    """Test that duplicate sources are deduplicated"""
    provider = MockSearchProvider()
    agent = ResearchAgent(provider)

    # Generate queries that might return duplicates
    queries = await agent.generate_queries("artificial intelligence")
    responses = await agent.collect_results(queries)

    # Manually create duplicate responses for testing
    if responses:
        responses.append(responses[0])

    sources = agent.rank_sources(responses, "artificial intelligence")

    # Check that URLs are unique
    urls = [s.url for s in sources]
    assert len(urls) == len(set(urls)), "Duplicate sources should be removed"


@pytest.mark.asyncio
async def test_source_ranking():
    """Test that sources are ranked by relevance"""
    provider = MockSearchProvider()
    agent = ResearchAgent(provider)

    result = await agent.research("climate change temperature")

    # Sources should be ordered by relevance
    if len(result.evidence) > 1:
        for i in range(len(result.evidence) - 1):
            assert result.evidence[i].relevance_score >= result.evidence[i + 1].relevance_score


@pytest.mark.asyncio
async def test_citation_preservation():
    """Test that citations are properly preserved"""
    provider = MockSearchProvider()
    agent = ResearchAgent(provider)

    result = await agent.research("What is AI?")

    for ev in result.evidence:
        assert ev.citation is not None
        assert ev.citation.source_type == EvidenceSource.WEB_RESEARCH
        assert ev.citation.url is not None
        assert ev.citation.title is not None
        assert ev.citation.timestamp is not None

        # Test citation formatting
        markdown = ev.citation.to_markdown()
        assert markdown.startswith("[")
        assert "](" in markdown


@pytest.mark.asyncio
async def test_insufficient_evidence():
    """Test handling when insufficient evidence is found"""
    provider = MockSearchProvider()
    agent = ResearchAgent(provider)

    # Query that returns minimal results
    result = await agent.research("zxcvbnmasdfghjkl nonexistent query")

    # Should still return a result, just with low confidence
    assert result is not None
    assert isinstance(result.evidence, list)

    # Check if result identifies insufficient evidence
    if not result.has_sufficient_evidence():
        assert result.confidence < 0.5


@pytest.mark.asyncio
async def test_search_failure_handling():
    """Test graceful handling of search failures"""

    class FailingProvider(MockSearchProvider):
        async def search(self, query: str, max_results: int = 10):
            raise Exception("Search API unavailable")

    provider = FailingProvider()
    agent = ResearchAgent(provider)

    result = await agent.research("test query")

    # Should return empty result, not crash
    assert result is not None
    assert len(result.evidence) == 0
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_evidence_extraction():
    """Test that evidence is extracted with proper metadata"""
    provider = MockSearchProvider()
    agent = ResearchAgent(provider)

    result = await agent.research("artificial intelligence")

    for ev in result.evidence:
        assert ev.content is not None
        assert ev.source_type == EvidenceSource.WEB_RESEARCH
        assert 0.0 <= ev.relevance_score <= 1.0
        assert "rank" in ev.metadata


@pytest.mark.asyncio
async def test_citation_formatting():
    """Test that citations can be formatted as markdown"""
    provider = MockSearchProvider()
    agent = ResearchAgent(provider)

    result = await agent.research("What is AI?")

    citations_md = result.format_citations()

    assert "Web Research" in citations_md
    assert "[" in citations_md
    assert "](" in citations_md


@pytest.mark.asyncio
async def test_confidence_calculation():
    """Test that confidence is calculated based on evidence quality"""
    provider = MockSearchProvider()
    agent = ResearchAgent(provider)

    result = await agent.research("artificial intelligence")

    # Confidence should reflect evidence quality
    if result.has_sufficient_evidence():
        assert result.confidence > 0.5
    else:
        assert result.confidence <= 0.5


@pytest.mark.asyncio
async def test_get_citations_by_type():
    """Test filtering citations by source type"""
    provider = MockSearchProvider()
    agent = ResearchAgent(provider)

    result = await agent.research("What is AI?")

    web_citations = result.get_citations_by_type(EvidenceSource.WEB_RESEARCH)

    assert len(web_citations) == len(result.evidence)
    assert all(c.source_type == EvidenceSource.WEB_RESEARCH for c in web_citations)

    # Should return empty for other types
    sql_citations = result.get_citations_by_type(EvidenceSource.SQL_QUERY)
    assert len(sql_citations) == 0
