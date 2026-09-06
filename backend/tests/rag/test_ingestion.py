"""Tests for the ingestion service using an in-memory database."""

from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.services.rag.embeddings.mock_embedder import MockEmbedder
from app.services.rag.ingestion import IngestionService


@pytest_asyncio.fixture
async def in_memory_session(monkeypatch):
    """SQLite async session for unit testing the ingestion service.

    The Chunk model's ``Vector`` column is pgvector-specific, so we patch the
    column type to a JSON-serialisable string for SQLite. We also create a
    stub ``tenants`` table so the foreign key on ``documents.tenant_id`` is
    satisfiable, then create only the RAG tables we exercise.
    """
    from sqlalchemy import Column, Integer, MetaData, String, Table

    from app.db.rag_models import Chunk, Document

    # Swap pgvector Vector column for a SQLite-friendly String.
    Chunk.__table__.c.embedding.type = String()

    metadata = MetaData()

    tenants = Table(
        "tenants",
        metadata,
        Column("id", Integer, primary_key=True),
    )
    # Re-declare documents and chunks against this metadata so FKs resolve.
    documents = Table(
        "documents",
        metadata,
        *[
            c.copy() for c in Document.__table__.columns
        ],
    )
    chunks = Table(
        "chunks",
        metadata,
        *[
            c.copy() for c in Chunk.__table__.columns
        ],
    )

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_ingest_text_file_creates_document_and_chunks(
    in_memory_session: AsyncSession, tmp_path: Path
):
    file_path = tmp_path / "sample.txt"
    file_path.write_text(
        "First paragraph about enterprise architecture.\n\n"
        "Second paragraph about retrieval augmented generation."
    )

    service = IngestionService(db=in_memory_session, embedder=MockEmbedder())
    result = await service.ingest(
        file_path=str(file_path),
        tenant_id=1,
        access_level=1,
        metadata={"uploader": "test"},
    )

    assert result.document_id > 0
    assert result.chunks_created >= 1
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_ingest_missing_file_raises_file_not_found(in_memory_session: AsyncSession):
    service = IngestionService(db=in_memory_session, embedder=MockEmbedder())
    with pytest.raises(FileNotFoundError):
        await service.ingest(
            file_path="/tmp/does-not-exist.txt",
            tenant_id=1,
        )


@pytest.mark.asyncio
async def test_ingest_unsupported_extension_raises(in_memory_session: AsyncSession, tmp_path: Path):
    file_path = tmp_path / "data.xyz"
    file_path.write_text("?")
    service = IngestionService(db=in_memory_session, embedder=MockEmbedder())
    with pytest.raises(ValueError, match="Unsupported file type"):
        await service.ingest(file_path=str(file_path), tenant_id=1)
