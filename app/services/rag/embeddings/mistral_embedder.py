from typing import List

import httpx
from app.core.config import settings
from app.services.rag.embeddings.base import BaseEmbedder


class MistralEmbedder(BaseEmbedder):
    """Mistral AI embedding provider (mistral-embed)."""

    def __init__(self, model: str = "mistral-embed", dimensions: int = 1024) -> None:
        self.model = model
        self.dimensions = dimensions
        self.api_key = settings.MISTRAL_API_KEY
        self.base_url = "https://api.mistral.ai/v1/embeddings"

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            raise RuntimeError("MISTRAL_API_KEY not set")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "input": texts},
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data.get("data", [])]
