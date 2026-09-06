"""Base embedding interface."""

from abc import ABC, abstractmethod
from typing import List


class BaseEmbedder(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            A list of embedding vectors (each a list of floats).
        """
        ...

    async def embed_query(self, text: str) -> List[float]:
        """Generate an embedding for a single query string.

        Default implementation delegates to embed_texts with a single item.

        Args:
            text: Query text to embed.

        Returns:
            An embedding vector.
        """
        results = await self.embed_texts([text])
        return results[0]
