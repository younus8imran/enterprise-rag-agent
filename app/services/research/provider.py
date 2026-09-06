from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime


class SearchResult(BaseModel):
    """Single search result from a provider"""
    title: str
    url: HttpUrl
    snippet: str
    rank: int
    provider: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Collection of search results"""
    query: str
    results: List[SearchResult]
    provider: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchProvider(ABC):
    """
    Abstract interface for web search providers.
    Decouples the application from any specific search API.
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 10
    ) -> SearchResponse:
        """
        Execute a search query and return results.

        Args:
            query: Natural language search query
            max_results: Maximum number of results to return

        Returns:
            SearchResponse with ranked results
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider's name for logging/tracking"""
        pass


class MockSearchProvider(SearchProvider):
    """
    Mock provider for testing without external API calls.
    Returns synthetic results based on query keywords.
    """

    def __init__(self):
        self._call_count = 0

    async def search(
        self,
        query: str,
        max_results: int = 10
    ) -> SearchResponse:
        """Generate mock results based on query keywords"""
        self._call_count += 1

        # Simulate different results based on query content
        if "artificial intelligence" in query.lower():
            results = [
                SearchResult(
                    title="What is Artificial Intelligence? | IBM",
                    url="https://www.ibm.com/topics/artificial-intelligence",
                    snippet="Artificial intelligence leverages computers and machines to mimic problem-solving and decision-making capabilities of the human mind.",
                    rank=1,
                    provider="mock",
                    metadata={"domain": "ibm.com"}
                ),
                SearchResult(
                    title="Artificial Intelligence (AI): What it is and why it matters | SAS",
                    url="https://www.sas.com/en_us/insights/analytics/what-is-artificial-intelligence.html",
                    snippet="Artificial intelligence (AI) makes it possible for machines to learn from experience, adjust to new inputs and perform human-like tasks.",
                    rank=2,
                    provider="mock",
                    metadata={"domain": "sas.com"}
                ),
            ]
        elif "climate change" in query.lower():
            results = [
                SearchResult(
                    title="Climate Change: Global Temperature | NOAA Climate.gov",
                    url="https://www.climate.gov/news-features/understanding-climate/climate-change-global-temperature",
                    snippet="Earth's temperature has risen by an average of 0.11° Fahrenheit per decade since 1850.",
                    rank=1,
                    provider="mock",
                    metadata={"domain": "climate.gov"}
                ),
                SearchResult(
                    title="Climate Change | United Nations",
                    url="https://www.un.org/en/climatechange/what-is-climate-change",
                    snippet="Climate change refers to long-term shifts in temperatures and weather patterns.",
                    rank=2,
                    provider="mock",
                    metadata={"domain": "un.org"}
                ),
            ]
        else:
            # Generic fallback
            results = [
                SearchResult(
                    title=f"Search result for: {query}",
                    url="https://example.com/result1",
                    snippet=f"This is a mock search result for the query: {query}",
                    rank=1,
                    provider="mock",
                    metadata={"domain": "example.com"}
                ),
            ]

        return SearchResponse(
            query=query,
            results=results[:max_results],
            provider="mock"
        )

    def get_provider_name(self) -> str:
        return "mock"

class TavilySearchProvider(SearchProvider):
    """
    Implementation of Tavily Search API.
    Tavily is optimized for LLM agents and research tasks.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.tavily.com/search"

    async def search(
        self,
        query: str,
        max_results: int = 10
    ) -> SearchResponse:
        """Execute search using Tavily API"""
        import httpx
        from app.core.logging import logger

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.base_url,
                    json={
                        "api_key": self.api_key,
                        "query": query,
                        "search_depth": "advanced",
                        "max_results": max_results,
                        "include_answer": True
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

                results = [
                    SearchResult(
                        title=r["title"],
                        url=r["url"],
                        snippet=r["content"],
                        rank=i + 1,
                        provider="tavily",
                        metadata=r.get("metadata", {})
                    )
                    for i, r in enumerate(data.get("results", []))
                ]

                return SearchResponse(
                    query=query,
                    results=results,
                    provider="tavily",
                    metadata={"answer": data.get("answer")}
                )
            except Exception as e:
                logger.error("tavily_search_failed", query=query, error=str(e))
                raise

    def get_provider_name(self) -> str:
        return "tavily"


class _NullSearchProvider(SearchProvider):
    """
    Silent no-op provider used when no real search backend is configured.
    Returns empty results instead of crashing.
    """

    async def search(self, query: str, max_results: int = 10) -> SearchResponse:
        return SearchResponse(query=query, results=[], provider="null")

    def get_provider_name(self) -> str:
        return "null"


def get_search_provider() -> SearchProvider:
    """
    Factory: returns TavilySearchProvider if TAVILY_API_KEY is set,
    otherwise a silent _NullSearchProvider.
    """
    from app.core.config import settings
    if settings.TAVILY_API_KEY:
        return TavilySearchProvider(api_key=settings.TAVILY_API_KEY)
    return _NullSearchProvider()
