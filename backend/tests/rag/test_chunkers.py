"""Tests for document chunking strategies."""

from app.services.rag.chunkers import (
    ChunkResult,
    FixedSizeChunker,
    SemanticChunker,
)


def test_fixed_chunker_produces_overlapping_chunks():
    text = "a" * 1000
    chunker = FixedSizeChunker(chunk_size=300, chunk_overlap=50)
    chunks = chunker.chunk(text)
    assert len(chunks) > 1
    assert all(isinstance(c, ChunkResult) for c in chunks)
    assert all(c.text for c in chunks)
    # Verify chunks are sequentially indexed
    indices = [c.index for c in chunks]
    assert indices == list(range(len(chunks)))


def test_fixed_chunker_rejects_invalid_overlap():
    import pytest

    with pytest.raises(ValueError):
        FixedSizeChunker(chunk_size=100, chunk_overlap=200)


def test_fixed_chunker_returns_empty_for_blank_text():
    chunker = FixedSizeChunker()
    assert chunker.chunk("   \n\n  ") == []


def test_semantic_chunker_merges_small_paragraphs():
    text = "Para one.\n\nPara two.\n\nPara three."
    chunker = SemanticChunker(max_chunk_size=1000, min_chunk_size=10)
    chunks = chunker.chunk(text)
    # Tiny paragraphs should merge into a single chunk.
    assert len(chunks) == 1
    assert "Para one" in chunks[0].text
    assert "Para three" in chunks[0].text


def test_semantic_chunker_splits_large_text():
    paragraphs = ["\n\n".join([f"Sentence {i}."] * 50) for i in range(10)]
    text = "\n\n".join(paragraphs)
    chunker = SemanticChunker(max_chunk_size=500, min_chunk_size=100)
    chunks = chunker.chunk(text)
    # Large input should produce multiple chunks.
    assert len(chunks) > 1


def test_chunkers_attach_metadata():
    text = "Hello world."
    chunks = FixedSizeChunker().chunk(text, metadata={"src": "unit-test"})
    assert chunks[0].metadata["src"] == "unit-test"
    assert chunks[0].metadata["chunk_strategy"] == "fixed_size"
