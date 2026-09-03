import pytest
import asyncio
from app.services.agent.graph import create_rag_graph
from app.services.agent.state import AgentState
from app.services.rag.service import RAGService
from app.services.sql.agent import SQLAgent
from app.services.research.agent import ResearchAgent
from app.services.research.provider import MockSearchProvider
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_rag():
    service = MagicMock(spec=RAGService)
    # Return a dummy document to simulate successful RAG retrieval
    dummy_doc = MagicMock()
    dummy_doc.content = "Internal AI Policy: All agents must be audited."
    dummy_doc.chunk_id = 123
    service.hybrid_search = AsyncMock(return_value=[dummy_doc])
    service.rerank = AsyncMock(return_value=[dummy_doc])
    return service

@pytest.fixture
def mock_sql():
    agent = MagicMock(spec=SQLAgent)
    agent.execute_query = AsyncMock(return_value="SQL Result Data")
    return agent

@pytest.fixture
def mock_research():
    provider = MockSearchProvider()
    return ResearchAgent(provider)

@pytest.fixture
def agent_graph(mock_rag, mock_sql, mock_research):
    return create_rag_graph(mock_rag, mock_sql, mock_research)

@pytest.mark.asyncio
async def test_rag_only_flow(agent_graph, mock_rag):
    # Query that triggers only RAG
    state = {"query": "What is the internal policy on AI?", "iterations": 0}
    result = await agent_graph.ainvoke(state)
    
    assert "Internal Docs" in result["answer"]
    assert "SQL Data" not in result["answer"]
    assert "Web Evidence" not in result["answer"]
    mock_rag.hybrid_search.assert_called()

@pytest.mark.asyncio
async def test_sql_only_flow(agent_graph, mock_sql):
    # Query that triggers only SQL
    state = {"query": "What was the revenue in Q1?", "iterations": 0}
    result = await agent_graph.ainvoke(state)
    
    assert "SQL Data" in result["answer"]
    assert "Internal Docs" not in result["answer"]
    assert "Web Evidence" not in result["answer"]
    mock_sql.execute_query.assert_called()

@pytest.mark.asyncio
async def test_web_only_flow(agent_graph):
    # Query that triggers only Web
    state = {"query": "What are the current global market trends for AI?", "iterations": 0}
    result = await agent_graph.ainvoke(state)
    
    assert "Web Evidence" in result["answer"]
    assert "Internal Docs" not in result["answer"]
    assert "SQL Data" not in result["answer"]

@pytest.mark.asyncio
async def test_hybrid_rag_sql_flow(agent_graph, mock_rag, mock_sql):
    # Query that triggers RAG + SQL
    state = {"query": "What is the revenue and the policy for reporting it?", "iterations": 0}
    result = await agent_graph.ainvoke(state)
    
    assert "Internal Docs" in result["answer"]
    assert "SQL Data" in result["answer"]
    mock_rag.hybrid_search.assert_called()
    mock_sql.execute_query.assert_called()

@pytest.mark.asyncio
async def test_hybrid_sql_web_flow(agent_graph, mock_sql):
    # Query that triggers SQL + Web
    state = {"query": "Compare our revenue to global market trends", "iterations": 0}
    result = await agent_graph.ainvoke(state)
    
    assert "SQL Data" in result["answer"]
    assert "Web Evidence" in result["answer"]
    mock_sql.execute_query.assert_called()

@pytest.mark.asyncio
async def test_full_hybrid_flow(agent_graph, mock_rag, mock_sql):
    # Query that triggers RAG + SQL + Web
    state = {"query": "Why did revenue decline and what do internal docs and market news say?", "iterations": 0}
    result = await agent_graph.ainvoke(state)
    
    assert "Internal Docs" in result["answer"]
    assert "SQL Data" in result["answer"]
    assert "Web Evidence" in result["answer"]
    mock_rag.hybrid_search.assert_called()
    mock_sql.execute_query.assert_called()
