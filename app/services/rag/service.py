from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.logging import logger

class RetrievalResult(BaseModel):
    content: str
    metadata: Dict[str, Any]
    score: float
    chunk_id: int

class RAGService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def embed_query(self, text: str) -> List[float]:
        """
        Generates embeddings for a query.
        In production, this calls an LLM API (e.g., Mistral, Cohere).
        """
        # Mocking embedding for now to allow the agent to run.
        # In real implementation, this would use settings.MISTRAL_API_KEY
        return [0.1] * 1536

    async def hybrid_search(self, query: str, filters: Optional[Dict] = None, top_k: int = 5) -> List[RetrievalResult]:
        """
        Implements Hybrid Retrieval: Vector Search + Keyword Search merged via RRF.
        """
        logger.info("performing_hybrid_search", query=query)

        # 1. Vector Search
        embedding = await self.embed_query(query)
        vector_query = text("""
            SELECT id, content, metadata_json, 1 - (embedding <=> :emb) as score
            FROM chunks
            WHERE tenant_id = :tid
            ORDER BY score DESC LIMIT :limit
        """)
        # Note: tenant_id would come from context/state
        res_vec = await self.db.execute(vector_query, {"emb": str(embedding), "tid": 1, "limit": top_k})

        # 2. Keyword Search (pg_trgm)
        keyword_query = text("""
            SELECT id, content, metadata_json, ts_rank_cd(to_tsvector('english', content), plainto_tsquery('english', :q)) as score
            FROM chunks
            WHERE tenant_id = :tid AND content % :q
            ORDER BY score DESC LIMIT :limit
        """)
        res_key = await self.db.execute(keyword_query, {"q": query, "tid": 1, "limit": top_k})

        # 3. Reciprocal Rank Fusion (RRF)
        # Simplified RRF for this implementation
        results = {}
        for i, row in enumerate(res_vec):
            results[row.id] = results.get(row.id, 0) + 1 / (60 + i + 1)
        for i, row in enumerate(res_key):
            results[row.id] = results.get(row.id, 0) + 1 / (60 + i + 1)

        # Fetch the top combined results
        top_ids = sorted(results, key=results.get, reverse=True)[:top_k]

        final_results = []
        if top_ids:
            final_res = await self.db.execute(
                text("SELECT id, content, metadata_json FROM chunks WHERE id = ANY(:ids)"),
                {"ids": top_ids}
            )
            for row in final_res:
                final_results.append(RetrievalResult(
                    content=row.content,
                    metadata=row.metadata_json or {},
                    score=results.get(row.id, 0),
                    chunk_id=row.id
                ))

        return final_results

    async def rerank(self, query: str, documents: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        Reranks documents using a Cross-Encoder.
        """
        if not documents:
            return []
        # Mocking reranking by shuffling or keeping order
        # In production, this calls a reranker model (e.g., BGE-Reranker)
        return documents
