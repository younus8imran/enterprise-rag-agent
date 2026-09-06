"""Fixed-size chunker with configurable overlap."""

from typing import Any, Dict, List, Optional

from app.services.rag.chunkers.base import BaseChunker, ChunkResult


class FixedSizeChunker(BaseChunker):
    """Splits text into fixed-size chunks with overlap.

    Args:
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Number of overlapping characters between consecutive chunks.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[ChunkResult]:
        """Split text into fixed-size chunks with overlap.

        Args:
            text: Full document text.
            metadata: Optional metadata to attach to each chunk.

        Returns:
            A list of ChunkResult instances.
        """
        if not text.strip():
            return []

        meta = metadata or {}
        chunks: List[ChunkResult] = []
        step = self.chunk_size - self.chunk_overlap
        start = 0
        index = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    ChunkResult(
                        text=chunk_text,
                        index=index,
                        metadata={**meta, "chunk_strategy": "fixed_size"},
                    )
                )
                index += 1
            start += step

        return chunks
