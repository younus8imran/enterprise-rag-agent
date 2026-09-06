"""Semantic chunker that splits on paragraph boundaries."""

import re
from typing import Any, Dict, List, Optional

from app.services.rag.chunkers.base import BaseChunker, ChunkResult

# Pattern to split on double newlines (paragraph boundaries)
_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")


class SemanticChunker(BaseChunker):
    """Splits text on paragraph boundaries, merging small paragraphs up to max_chunk_size.

    Args:
        max_chunk_size: Maximum characters per chunk.
        min_chunk_size: Minimum characters; paragraphs smaller than this are merged.
    """

    def __init__(self, max_chunk_size: int = 1500, min_chunk_size: int = 200) -> None:
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[ChunkResult]:
        """Split text on paragraph boundaries, merging small sections.

        Args:
            text: Full document text.
            metadata: Optional metadata to attach to each chunk.

        Returns:
            A list of ChunkResult instances.
        """
        if not text.strip():
            return []

        meta = metadata or {}
        paragraphs = [p.strip() for p in _PARAGRAPH_SPLIT.split(text) if p.strip()]

        chunks: List[ChunkResult] = []
        buffer: List[str] = []
        buffer_len = 0
        index = 0

        for para in paragraphs:
            # If adding this paragraph exceeds max size, flush the buffer
            if buffer and buffer_len + len(para) > self.max_chunk_size:
                chunks.append(
                    ChunkResult(
                        text="\n\n".join(buffer),
                        index=index,
                        metadata={**meta, "chunk_strategy": "semantic"},
                    )
                )
                index += 1
                buffer = []
                buffer_len = 0

            # If a single paragraph exceeds max size, emit it directly
            if len(para) > self.max_chunk_size:
                if buffer:
                    chunks.append(
                        ChunkResult(
                            text="\n\n".join(buffer),
                            index=index,
                            metadata={**meta, "chunk_strategy": "semantic"},
                        )
                    )
                    index += 1
                    buffer = []
                    buffer_len = 0
                chunks.append(
                    ChunkResult(
                        text=para,
                        index=index,
                        metadata={**meta, "chunk_strategy": "semantic"},
                    )
                )
                index += 1
                continue

            buffer.append(para)
            buffer_len += len(para)

        # Flush remaining buffer
        if buffer:
            chunks.append(
                ChunkResult(
                    text="\n\n".join(buffer),
                    index=index,
                    metadata={**meta, "chunk_strategy": "semantic"},
                )
            )

        return chunks
