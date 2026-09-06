"""Mock embedder for testing and development."""

import hashlib
import math
from typing import List

from app.services.rag.embeddings.base import BaseEmbedder


class MockEmbedder(BaseEmbedder):
    """Generates deterministic pseudo-embeddings from text content.

    Produces consistent 1536-dimensional vectors derived from a hash of the input
    text, so the same text always yields the same embedding. This is far more useful
    for testing than a flat ``[0.1] * 1536`` vector because similar texts produce
    *different* vectors, allowing vector-search logic to be exercised.

    Args:
        dimensions: Length of the embedding vector. Defaults to 1536.
    """

    def __init__(self, dimensions: int = 1536) -> None:
        self.dimensions = dimensions

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate deterministic embeddings for a list of texts.

        Args:
            texts: Texts to embed.

        Returns:
            A list of embedding vectors.
        """
        return [self._deterministic_vector(t) for t in texts]

    def _deterministic_vector(self, text: str) -> List[float]:
        """Produce a unit-length vector seeded by the SHA-256 of *text*."""
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        # Expand the 64-hex-char digest to fill `dimensions` slots.
        raw: List[float] = []
        for i in range(self.dimensions):
            # Cycle through digest chars; convert to a float in (-1, 1).
            char_idx = i % len(digest)
            val = (int(digest[char_idx], 16) - 7.5) / 7.5
            # Add a small perturbation from the position so nearby indices differ.
            val += math.sin(i * 0.1) * 0.01
            raw.append(val)

        # L2-normalise so cosine similarity works correctly.
        norm = math.sqrt(sum(v * v for v in raw)) or 1.0
        return [v / norm for v in raw]
