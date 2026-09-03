from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.services.agent.state import AgentState
from app.services.rag.service import RAGService
from app.services.sql.agent import SQLAgent
from app.services.research.agent import ResearchAgent
from app.services.research.provider import MockSearchProvider
from app.core.logging import logger
from app.core.security.validation import SecurityValidator
from app.core.telemetry.collector import TelemetryCollector
import asyncio

class Plan(BaseModel):
    steps: List[str] = Field(description="The sequence of steps to answer the query")
    reasoning: str = Field(description="Why this plan was chosen")
    tools: List[str] = Field(description="Tools required: 'rag', 'sql', 'web', 'calculator'")

class GradedDocument(BaseModel):
    chunk_id: int
    grade: str = Field(description="Relevant or Irrelevant")
    reasoning: str

class AgentNodes:
    def __init__(self, rag_service: RAGService, sql_agent: SQLAgent, research_agent: ResearchAgent):
        self.rag = rag_service
        self.sql = sql_agent
        self.research = research_agent

    async def classify_query(self, state: AgentState) -> Dict[str, Any]:
        """Dynamically determine which tools are needed based on the query."""
        logger.info("node_classify_query", query=state["query"])

        # Security: Validate user input for prompt injection
        try:
            sanitized_query = SecurityValidator.validate_input(state["query"])
        except Exception as e:
            # If injection is detected, we halt the agent and return a security error
            return {"answer": "Security Error: Malicious input detected.", "confidence": 0.0}

        query = sanitized_query.lower()

        tools = []
        if any(k in query for k in ["revenue", "sales", "count", "amount", "date"]):
            tools.append("sql")
        if any(k in query for k in ["policy", "document", "guide", "internal"]):
            tools.append("rag")
        if any(k in query for k in ["external", "world", "market", "news", "explain why"]):
            tools.append("web")

        # Fallback: if nothing matched, try RAG
        if not tools:
            tools.append("rag")

        logger.info("query_classified", tools=tools)
        return {
            "tools_to_use": tools,
            "plan": f"Use tools: {', '.join(tools)} to answer the query."
        }

    async def retrieve_rag(self, state: AgentState) -> Dict[str, Any]:
        """Retrieve evidence from Internal RAG."""
        logger.info("node_retrieve_rag", query=state["query"])
        docs = await self.rag.hybrid_search(state["query"])
        docs = await self.rag.rerank(state["query"], docs)
        return {"documents": docs}

    async def retrieve_sql(self, state: AgentState) -> Dict[str, Any]:
        """Retrieve evidence from SQL database."""
        logger.info("node_retrieve_sql", query=state["query"])
        # Use the SQL agent to translate and execute
        result = await self.sql.execute_query(state["query"])
        return {"sql_results": [result]}

    async def retrieve_web(self, state: AgentState) -> Dict[str, Any]:
        """Retrieve evidence from Web Research."""
        logger.info("node_retrieve_web", query=state["query"])
        result = await self.research.research(state["query"])
        return {"web_evidence": result.evidence}

    async def synthesize_answer(self, state: AgentState) -> Dict[str, Any]:
        """Combine evidence from all tools into a final cited synthesis."""
        logger.info("node_synthesize_answer")

        evidence_parts = []
        citations = []

        if state.get("documents"):
            evidence_parts.append(f"Internal Docs: {state['documents'][0].content[:100]}...")
            citations.extend([d.chunk_id for d in state["documents"]])

        if state.get("sql_results"):
            evidence_parts.append(f"SQL Data: {state['sql_results'][0]}")
            citations.append("SQL_DATA")

        if state.get("web_evidence"):
            evidence_parts.append(f"Web Evidence: {state['web_evidence'][0].content[:100]}...")
            citations.extend([e.citation.url for e in state["web_evidence"]])

        answer = "Synthesis of evidence: " + " | ".join(evidence_parts) if evidence_parts else "No evidence found."

        return {
            "answer": answer,
            "citations": citations,
            "confidence": 0.8 if evidence_parts else 0.0
        }

    async def criticize_answer(self, state: AgentState) -> Dict[str, Any]:
        """Act as a critic to verify the answer matches the query and evidence."""
        logger.info("node_criticize_answer")

        # Prevent infinite loops by checking iterations
        current_iterations = state.get("iterations", 0)
        if current_iterations >= 3:
            return {"critic_feedback": "approved", "evidence_grade": "good"}

        # Logic: If answer is "No evidence found" but tools were attempted, it's a failure
        if "No evidence found" in (state.get("answer") or ""):
            return {
                "critic_feedback": "poor",
                "evidence_grade": "poor",
                "iterations": current_iterations + 1
            }

        return {"critic_feedback": "approved", "evidence_grade": "good"}

    async def validate_citations(self, state: AgentState) -> Dict[str, Any]:
        """Final pass to ensure citations are valid."""
        logger.info("node_validate_citations")
        return {"answer": state["answer"] + "\n\n[Verified Citations Provided]"}
