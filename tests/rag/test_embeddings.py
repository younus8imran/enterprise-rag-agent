"""Tests for embedding providers."""

import pytest

from app.services.rag.embeddings import BaseEmbedder, MockEmbedder


@pytest.mark.asyncio
async def test_mock_embedder_returns_1536_dim_vectors():
    embedder = MockEmbedder()
    vectors = await embedder.embed_texts(["hello", "world"])
    assert len(vectors) == 2
    assert all(len(v) == 1536 for v in vectors)


@pytest.mark.asyncio
async def test_mock_embedder_is_deterministic():
    embedder = MockEmbedder()
    v1 = await embedder.embed_texts(["hello world"])
    v2 = await embedder.embed_texts(["hello world"])
    assert v1 == v2


@pytest.mark.asyncio
async def test_mock_embedder_produces_unit_vectors():
    import math

    embedder = MockEmbedder()
    vectors = await embedder.embed_texts(["sample text"])
    norm = math.sqrt(sum(v * v for v in vectors[0]))
    assert abs(norm - 1.0) < 1e-6


@pytest.mark.asyncio
async def test_mock_embedder_distinguishes_texts():
    embedder = MockEmbedder()
    a, b = await embedder.embed_texts(["alpha", "completely different beta"])
    assert a != b


@pytest.mark.asyncio
async def test_embed_query_delegates_to_batch():
    embedder = MockEmbedder()
    q = await embedder.embed_query("single")
    batch = (await embedder.embed_texts(["single"]))[0]
    assert q == batch
