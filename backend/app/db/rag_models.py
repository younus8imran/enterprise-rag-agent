from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False) # pdf, md, txt, csv
    source = Column(String)
    metadata_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1024), nullable=False)

    # Structured metadata for filtering
    page = Column(Integer)
    section = Column(String)
    department = Column(String, index=True)
    access_level = Column(Integer, default=0, index=True)

    metadata_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    document = relationship("Document")

# Index for vector search
# pgvector HNSW index syntax for SQLAlchemy requires passing the opclass in postgresql_with or through a custom Index implementation
# However, for basic autogenerate, we'll use a simpler Index and add the opclass via a migration script manually if needed.
Index("idx_chunks_embedding", Chunk.embedding, postgresql_using="hnsw")

# Index for keyword search
Index("idx_chunks_content_gin", Chunk.content, postgresql_using="gin")
