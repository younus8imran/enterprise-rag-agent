"""Base chunker interface and shared data models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ChunkResult:
    """A single chunk produced from a document."""

    text: str
    index: int
    page: Optional[int] = None
    section: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def char_count(self) -> int:
        return len(self.text)


class BaseChunker(ABC):
    """Abstract base class for document chunkers."""

    @abstractmethod
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[ChunkResult]:
        """Split text into chunks.

        Args:
            text: Full document text to split.
            metadata: Optional metadata to propagate to each chunk.

        Returns:
            A list of ChunkResult instances.
        """
        ...
