import pytest
import asyncio
from app.services.agent.graph import create_rag_graph
from app.services.rag.service import RAGService
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import settings

def get_rag_service():
    class MockResult:
        def __iter__(self):
            return iter([])
        def all(self): return []
        def scalar(self): return None

    class MockSession:
        async def execute(self, text, params=None):
            return MockResult()
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass

    return RAGService(MockSession())

@pytest.mark.asyncio
async def test_agent_routing_flow():
    rag_service = get_rag_service()
    graph = create_rag_graph(rag_service)
    initial_state = {
        "query": "What is the revenue for Q3?",
        "documents": [],
        "citations": [],
        "iterations": 0
    }

    # Run the graph
    result = await graph.ainvoke(initial_state)

    assert "answer" in result
    assert "citations" in result
    assert result["iterations"] >= 0

@pytest.mark.asyncio
async def test_retry_behavior():
    rag_service = get_rag_service()
    from app.services.agent.nodes import AgentNodes
    nodes = AgentNodes(rag_service)

    state = {
        "query": "Test",
        "documents": [],
        "citations": [],
        "iterations": 0,
        "evidence_grade": "poor"
    }
    res = await nodes.rewrite_query(state)
    assert res["iterations"] == 1
