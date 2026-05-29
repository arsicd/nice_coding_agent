from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Index, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from search.ml_models import CODE_EMBEDDING_DIM, DOC_EMBEDDING_DIM


class Base(DeclarativeBase):
    pass


class CodeChunk(Base):
    __tablename__ = "code_chunks"

    # Unique ID format: "file_path::chunk_type::chunk_name::index"
    id: Mapped[str] = mapped_column(String, primary_key=True)

    # Tree Metadata
    parent_file: Mapped[str] = mapped_column(String, nullable=False)
    chunk_type: Mapped[str] = mapped_column(String, nullable=False)
    chunk_name: Mapped[str] = mapped_column(String, nullable=False)

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    file_signatures: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(CODE_EMBEDDING_DIM))

    __table_args__ = (
        # 1. pgvector HNSW Index for fast semantic similarity search.
        # Cosine ops — embeddings are L2-normalized at write/query time.
        Index(
            "code_chunks_embedding_idx",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 200},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        # 2. ParadeDB pg_search BM25 Index for fast keyword matching
        # This acts as a covering index for the text fields we want to search
        Index(
            "code_chunks_bm25_idx",
            "id",
            "chunk_name",
            "content",
            "file_signatures",
            postgresql_using="bm25",
            postgresql_with={"key_field": "id"},
        ),
        Index("code_chunks_parent_file_idx", "parent_file"),
    )


class IndexedFile(Base):
    __tablename__ = "indexed_files"

    parent_file: Mapped[str] = mapped_column(String, primary_key=True)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    indexed_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    # Unique ID format: "file_path::doc::index"
    id: Mapped[str] = mapped_column(String, primary_key=True)

    parent_file: Mapped[str] = mapped_column(String, nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(DOC_EMBEDDING_DIM))

    __table_args__ = (
        Index(
            "document_chunks_embedding_idx",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 200},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index(
            "document_chunks_bm25_idx",
            "id",
            "content",
            "parent_file",
            postgresql_using="bm25",
            postgresql_with={"key_field": "id"},
        ),
        Index("document_chunks_parent_file_idx", "parent_file"),
    )


class IndexedDocument(Base):
    __tablename__ = "indexed_documents"

    parent_file: Mapped[str] = mapped_column(String, primary_key=True)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    indexed_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
