from typing import List, Optional, Annotated, TypedDict, Dict, Any
from pydantic import BaseModel, Field
import operator

class RetrievalDoc(BaseModel):
    content: str
    metadata: dict
    score: float
    chunk_id: int

class AgentState(TypedDict):
    # The original user query
    query: str
    # Rewritten query for better retrieval
    rewritten_query: Optional[str]
    # The plan for how to answer the query
    plan: Optional[str]
    # Detailed plan: which tools to use
    tools_to_use: List[str]
    # Retrieved documents (Internal RAG)
    documents: Annotated[List[RetrievalDoc], operator.add]
    # SQL query results
    sql_results: Annotated[List[Any], operator.add]
    # Web research evidence
    web_evidence: Annotated[List[Any], operator.add]
    # Grading of the retrieved evidence
    evidence_grade: Optional[str] # "good", "poor"
    # The generated answer
    answer: Optional[str]
    # Citations and references
    citations: Annotated[List[Any], operator.add]
    # Confidence score
    confidence: float
    # Iteration count to prevent infinite loops
    iterations: int
    # Critic feedback
    critic_feedback: Optional[str]
