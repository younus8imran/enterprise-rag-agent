from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.services.research.provider import SearchProvider, SearchResponse
from app.services.llm.mistral_chat import MistralChatProvider
from app.services.research.evidence import (
    Evidence,
    EvidenceSource,
    Citation,
    ResearchResult,
)
from app.core.logging import logger


class ResearchQuery(BaseModel):
    """Generated search query with intent"""
    query: str
    intent: str
    priority: int = Field(ge=1, le=10, default=5)


class WebSource(BaseModel):
    """Ranked web source with extracted content"""
    url: str
    title: str
    content: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    rank: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResearchAgent:
    """
    Web research agent with multi-query generation,
    source ranking, and evidence extraction.
    """

    def __init__(self, search_provider: SearchProvider):
        self.search_provider = search_provider
        self.max_queries = 3
        self.max_sources_per_query = 5

    async def generate_queries(
        self,
        question: str,
        context: Optional[str] = None
    ) -> List[ResearchQuery]:
        """
        Generate multiple search queries for complex questions.

        For complex questions, breaks down into sub-queries.
        For simple questions, returns a single refined query.

        Args:
            question: Original user question
            context: Optional context to refine queries

        Returns:
            List of research queries ordered by priority
        """
        logger.info("generating_research_queries", question=question)
        chat = MistralChatProvider()
        system_msg = (
            "Generate up to 3 precise web-search queries. Return only the queries, "
            "one per line, with no numbering, no explanation, no markdown fences."
        )
        # Pass user's question as query, system instruction guides format
        response = await chat.generate_answer(query=question, system_prompt=system_msg) or question
        queries_text = [q.strip() for q in response.split("\n") if q.strip()]
        queries = [ResearchQuery(query=q, intent="direct_answer", priority=1) for q in queries_text[:3]]
        return queries[:self.max_queries]

    async def search(self, query: ResearchQuery) -> SearchResponse:
        """Execute search via provider"""
        logger.info("executing_search", query=query.query, intent=query.intent)
        return await self.search_provider.search(
            query.query,
            max_results=self.max_sources_per_query
        )

    async def collect_results(
        self,
        queries: List[ResearchQuery]
    ) -> List[SearchResponse]:
        """
        Execute all queries and collect results.

        Args:
            queries: List of research queries

        Returns:
            List of search responses
        """
        results = []
        for query in queries:
            try:
                response = await self.search(query)
                results.append(response)
            except Exception as e:
                logger.error(
                    "search_failed",
                    query=query.query,
                    error=str(e)
                )
                # Continue with other queries

        return results

    def rank_sources(
        self,
        responses: List[SearchResponse],
        question: str
    ) -> List[WebSource]:
        """
        Rank and deduplicate sources across all search results.

        Args:
            responses: All search responses
            question: Original question for relevance scoring

        Returns:
            Deduplicated and ranked sources
        """
        logger.info("ranking_sources", response_count=len(responses))

        sources_by_url = {}

        for response in responses:
            for result in response.results:
                url = str(result.url)

                if url in sources_by_url:
                    # Duplicate source - keep highest rank
                    existing = sources_by_url[url]
                    if result.rank < existing.rank:
                        sources_by_url[url].rank = result.rank
                else:
                    # New source
                    relevance = self._calculate_relevance(
                        result.snippet,
                        question
                    )
                    sources_by_url[url] = WebSource(
                        url=url,
                        title=result.title,
                        content=result.snippet,
                        relevance_score=relevance,
                        rank=result.rank,
                        metadata=result.metadata
                    )

        # Sort by relevance score, then rank
        ranked = sorted(
            sources_by_url.values(),
            key=lambda s: (-s.relevance_score, s.rank)
        )

        logger.info(
            "sources_ranked",
            total_sources=len(ranked),
            duplicates_removed=len(responses) * self.max_sources_per_query - len(ranked)
        )

        return ranked

    def _calculate_relevance(self, content: str, question: str) -> float:
        """
        Calculate relevance score between content and question.

        In production, this would use embedding similarity or LLM scoring.
        For now, use keyword overlap as a simple heuristic.

        Args:
            content: Source content
            question: Original question

        Returns:
            Relevance score [0.0, 1.0]
        """
        question_words = set(question.lower().split())
        content_words = set(content.lower().split())

        # Remove common stop words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "what", "how", "why"}
        question_words -= stop_words
        content_words -= stop_words

        if not question_words:
            return 0.5

        overlap = len(question_words & content_words)
        score = overlap / len(question_words)

        return min(score, 1.0)

    async def extract_evidence(
        self,
        sources: List[WebSource],
        question: str,
        max_evidence: int = 5
    ) -> List[Evidence]:
        """
        Extract relevant evidence from ranked sources.

        Args:
            sources: Ranked web sources
            question: Original question
            max_evidence: Maximum evidence items to extract

        Returns:
            List of evidence with citations
        """
        logger.info("extracting_evidence", source_count=len(sources))

        evidence = []

        for source in sources[:max_evidence]:
            # In production, use LLM to extract relevant passages
            # For now, use the snippet as evidence
            citation = Citation(
                source_type=EvidenceSource.WEB_RESEARCH,
                content=source.content,
                url=source.url,
                title=source.title,
                metadata={
                    "rank": source.rank,
                    "domain": source.metadata.get("domain", "unknown")
                }
            )

            evidence.append(
                Evidence(
                    content=source.content,
                    source_type=EvidenceSource.WEB_RESEARCH,
                    citation=citation,
                    relevance_score=source.relevance_score,
                    metadata={"rank": source.rank}
                )
            )

        logger.info("evidence_extracted", evidence_count=len(evidence))

        return evidence

    async def research(
        self,
        question: str,
        context: Optional[str] = None
    ) -> ResearchResult:
        """
        Full research pipeline: query generation → search → ranking → extraction.

        Args:
            question: Research question
            context: Optional context

        Returns:
            Complete research result with evidence and citations
        """
        logger.info("research_started", question=question)

        # 1. Generate queries
        queries = await self.generate_queries(question, context)

        # 2. Execute searches
        responses = await self.collect_results(queries)

        if not responses:
            logger.warning("no_search_results", question=question)
            return ResearchResult(
                query=question,
                evidence=[],
                confidence=0.0,
                sources_consulted={EvidenceSource.WEB_RESEARCH: 0}
            )

        # 3. Rank and deduplicate sources
        sources = self.rank_sources(responses, question)

        if not sources:
            logger.warning("no_sources_after_ranking", question=question)
            return ResearchResult(
                query=question,
                evidence=[],
                confidence=0.0,
                sources_consulted={EvidenceSource.WEB_RESEARCH: 0}
            )

        # 4. Extract evidence
        evidence = await self.extract_evidence(sources, question)

        # 5. Calculate confidence
        confidence = self._calculate_confidence(evidence)

        result = ResearchResult(
            query=question,
            evidence=evidence,
            confidence=confidence,
            sources_consulted={
                EvidenceSource.WEB_RESEARCH: len(sources)
            },
            metadata={
                "queries_generated": len(queries),
                "total_results": sum(len(r.results) for r in responses),
                "unique_sources": len(sources)
            }
        )

        logger.info(
            "research_completed",
            evidence_count=len(evidence),
            confidence=confidence,
            sources=len(sources)
        )

        return result

    def _calculate_confidence(self, evidence: List[Evidence]) -> float:
        """
        Calculate overall confidence based on evidence quality.

        Args:
            evidence: Extracted evidence

        Returns:
            Confidence score [0.0, 1.0]
        """
        if not evidence:
            return 0.0

        # Average relevance scores
        avg_relevance = sum(e.relevance_score for e in evidence) / len(evidence)

        # Boost confidence with more sources
        source_bonus = min(len(evidence) / 5.0, 1.0) * 0.2

        confidence = min(avg_relevance + source_bonus, 1.0)

        # Penalty for having very few sources
        if len(evidence) < 2:
            confidence *= 0.4

        return confidence
