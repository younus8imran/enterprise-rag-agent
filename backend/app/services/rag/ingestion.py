"""Document ingestion pipeline: parse → chunk → embed → store."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.rag_models import Chunk, Document
from app.services.rag.chunkers.base import BaseChunker, ChunkResult
from app.services.rag.chunkers.semantic_chunker import SemanticChunker
from app.services.rag.embeddings.base import BaseEmbedder
from app.services.rag.embeddings.mistral_embedder import MistralEmbedder
from app.services.rag.parsers.base import ParsedDocument
from app.services.rag.parsers.registry import get_parser


class IngestionResult:
    """Encapsulates the outcome of a document ingestion run."""

    def __init__(self, document_id: int, chunks_created: int, status: str) -> None:
        self.document_id = document_id
        self.chunks_created = chunks_created
        self.status = status


class IngestionService:
    """Orchestrates parsing, chunking, embedding, and storage of documents.

    Args:
        db: Async SQLAlchemy session.
        embedder: Embedding provider. Falls back to ``MistralEmbedder`` when *None*.
        chunker: Chunking strategy. Falls back to ``SemanticChunker`` when *None*.
        embed_batch_size: Number of chunks to embed in a single call.
    """

    def __init__(
        self,
        db: AsyncSession,
        embedder: Optional[BaseEmbedder] = None,
        chunker: Optional[BaseChunker] = None,
        embed_batch_size: int = 64,
    ) -> None:
        self.db = db
        self.embedder = embedder or MistralEmbedder()
        self.chunker = chunker or SemanticChunker()
        self.embed_batch_size = embed_batch_size

    async def ingest(
        self,
        file_path: str,
        tenant_id: int,
        access_level: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestionResult:
        """Run the full ingestion pipeline for a single document.

        Args:
            file_path: Path to the document file on disk.
            tenant_id: Tenant that owns the document (row-level isolation).
            access_level: Visibility tier (1=Basic, 2=Confidential, 3=Top Secret).
            metadata: Arbitrary metadata to store alongside the document.

        Returns:
            An ``IngestionResult`` with the document id, chunk count, and status.

        Raises:
            FileNotFoundError: If *file_path* does not exist.
            ValueError: If the file type is unsupported.
        """
        path = Path(file_path)
        meta = metadata or {}

        logger.info(
            "ingestion_pipeline_start",
            file_path=str(path),
            tenant_id=tenant_id,
        )

        # 1. Parse ----------------------------------------------------------------
        parser = get_parser(path)
        parsed: ParsedDocument = await parser.parse(path)
        logger.info(
            "document_parsed",
            name=parsed.name,
            doc_type=parsed.doc_type,
            pages=parsed.total_pages,
        )

        # 2. Create the Document row ---------------------------------------------
        document = Document(
            tenant_id=tenant_id,
            name=parsed.name,
            type=parsed.doc_type,
            source=str(path),
            metadata_json={**meta, "total_pages": parsed.total_pages},
        )
        self.db.add(document)
        await self.db.flush()  # Populate document.id

        # 3. Chunk ----------------------------------------------------------------
        chunk_results: List[ChunkResult] = self.chunker.chunk(
            parsed.full_text,
            metadata={
                "source": str(path),
                "doc_type": parsed.doc_type,
            },
        )
        logger.info("document_chunked", chunks=len(chunk_results))

        if not chunk_results:
            await self.db.commit()
            return IngestionResult(
                document_id=document.id,
                chunks_created=0,
                status="completed",
            )

        # 4. Embed (batched) ------------------------------------------------------
        texts = [c.text for c in chunk_results]
        all_embeddings: List[List[float]] = []
        for start in range(0, len(texts), self.embed_batch_size):
            batch = texts[start : start + self.embed_batch_size]
            batch_embeddings = await self.embedder.embed_texts(batch)
            all_embeddings.extend(batch_embeddings)

        logger.info("embeddings_generated", total=len(all_embeddings))

        # 5. Store chunks in pgvector ---------------------------------------------
        for chunk_res, embedding in zip(chunk_results, all_embeddings):
            chunk_row = Chunk(
                document_id=document.id,
                tenant_id=tenant_id,
                content=chunk_res.text,
                embedding=embedding,
                page=chunk_res.page,
                section=chunk_res.section,
                access_level=access_level,
                metadata_json=chunk_res.metadata,
            )
            self.db.add(chunk_row)

        await self.db.commit()
        logger.info(
            "ingestion_pipeline_complete",
            document_id=document.id,
            chunks_created=len(chunk_results),
        )

        return IngestionResult(
            document_id=document.id,
            chunks_created=len(chunk_results),
            status="completed",
        )
