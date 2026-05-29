from typing import Iterable

from pgvector.sqlalchemy import Vector
from sqlalchemy import bindparam, delete, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from search.db.models import (
    CodeChunk,
    DocumentChunk,
    IndexedDocument,
    IndexedFile,
)
from search.ml_models import CODE_EMBEDDING_DIM, DOC_EMBEDDING_DIM


class CodeChunkRepository:
    def __init__(self, session: Session):
        self.session = session

    def delete_by_parent_file(self, parent_file: str) -> int:
        stmt = delete(CodeChunk).where(CodeChunk.parent_file == parent_file)
        result = self.session.execute(stmt)
        return result.rowcount or 0

    def insert_chunks(self, chunks: Iterable[CodeChunk]) -> int:
        chunks = list(chunks)
        if not chunks:
            return 0
        self.session.add_all(chunks)
        return len(chunks)

    def get_indexed_hash(self, parent_file: str) -> str | None:
        stmt = select(IndexedFile.content_hash).where(
            IndexedFile.parent_file == parent_file
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def upsert_indexed_file(self, parent_file: str, content_hash: str) -> None:
        stmt = pg_insert(IndexedFile).values(
            parent_file=parent_file, content_hash=content_hash
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[IndexedFile.parent_file],
            set_={
                "content_hash": stmt.excluded.content_hash,
                "indexed_at": text("now()"),
            },
        )
        self.session.execute(stmt)

    def delete_indexed_file(self, parent_file: str) -> int:
        stmt = delete(IndexedFile).where(IndexedFile.parent_file == parent_file)
        result = self.session.execute(stmt)
        return result.rowcount or 0

    def list_indexed_files(self) -> list[str]:
        stmt = select(IndexedFile.parent_file)
        return [row for row in self.session.execute(stmt).scalars().all()]

    def hybrid_search(
        self,
        query_text: str,
        query_embedding: list[float],
        fetch_n: int = 10,
        candidate_pool: int = 100,
        rrf_k: int = 60,
    ) -> list[dict]:
        """
        Run BM25 + vector ANN in parallel and fuse with Reciprocal Rank Fusion.

        Each candidate gets a score of:
            sum over both rankers of 1 / (rrf_k + rank_in_that_ranker)
        Candidates missing from one ranker simply contribute 0 from that side.
        rrf_k=60 is the standard literature default; higher values flatten
        the contribution of top ranks, lower values sharpen it.

        candidate_pool is how wide a net each ranker casts before fusion —
        wider improves recall at near-zero cost (BM25 + HNSW are both cheap).
        fetch_n is how many fused rows we return to the cross-encoder, which
        is the expensive stage, so we keep that tighter.
        """
        sql = text("""
            WITH bm25 AS (
                SELECT id, content, chunk_name, parent_file, chunk_type,
                       file_signatures,
                       ROW_NUMBER() OVER (ORDER BY paradedb.score(id) DESC) AS rank
                FROM code_chunks
                WHERE id @@@ paradedb.boolean(
                    should => ARRAY[
                        paradedb.match('content', :q),
                        paradedb.match('chunk_name', :q),
                        paradedb.match('file_signatures', :q)
                    ]
                )
                ORDER BY paradedb.score(id) DESC
                LIMIT :candidate_pool
            ),
            vec AS (
                SELECT id, content, chunk_name, parent_file, chunk_type,
                       file_signatures,
                       ROW_NUMBER() OVER (ORDER BY embedding <=> :emb) AS rank
                FROM code_chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> :emb
                LIMIT :candidate_pool
            ),
            fused AS (
                SELECT
                    COALESCE(b.id, v.id) AS id,
                    COALESCE(b.content, v.content) AS content,
                    COALESCE(b.chunk_name, v.chunk_name) AS chunk_name,
                    COALESCE(b.parent_file, v.parent_file) AS parent_file,
                    COALESCE(b.chunk_type, v.chunk_type) AS chunk_type,
                    COALESCE(b.file_signatures, v.file_signatures) AS file_signatures,
                    COALESCE(1.0 / (:rrf_k + b.rank), 0.0)
                  + COALESCE(1.0 / (:rrf_k + v.rank), 0.0) AS rrf_score
                FROM bm25 b
                FULL OUTER JOIN vec v ON b.id = v.id
            )
            SELECT id, content, chunk_name, parent_file, chunk_type,
                   file_signatures, rrf_score
            FROM fused
            ORDER BY rrf_score DESC
            LIMIT :fetch_n
            """).bindparams(bindparam("emb", type_=Vector(CODE_EMBEDDING_DIM)))

        rows = (
            self.session.execute(
                sql,
                {
                    "q": query_text,
                    "emb": query_embedding,
                    "fetch_n": fetch_n,
                    "candidate_pool": candidate_pool,
                    "rrf_k": rrf_k,
                },
            )
            .mappings()
            .all()
        )

        return [dict(row) for row in rows]


class DocumentChunkRepository:
    def __init__(self, session: Session):
        self.session = session

    def delete_by_parent_file(self, parent_file: str) -> int:
        stmt = delete(DocumentChunk).where(DocumentChunk.parent_file == parent_file)
        result = self.session.execute(stmt)
        return result.rowcount or 0

    def insert_chunks(self, chunks: Iterable[DocumentChunk]) -> int:
        chunks = list(chunks)
        if not chunks:
            return 0
        self.session.add_all(chunks)
        return len(chunks)

    def get_indexed_hash(self, parent_file: str) -> str | None:
        stmt = select(IndexedDocument.content_hash).where(
            IndexedDocument.parent_file == parent_file
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def upsert_indexed_document(self, parent_file: str, content_hash: str) -> None:
        stmt = pg_insert(IndexedDocument).values(
            parent_file=parent_file, content_hash=content_hash
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[IndexedDocument.parent_file],
            set_={
                "content_hash": stmt.excluded.content_hash,
                "indexed_at": text("now()"),
            },
        )
        self.session.execute(stmt)

    def delete_indexed_document(self, parent_file: str) -> int:
        stmt = delete(IndexedDocument).where(IndexedDocument.parent_file == parent_file)
        result = self.session.execute(stmt)
        return result.rowcount or 0

    def list_indexed_documents(self) -> list[str]:
        stmt = select(IndexedDocument.parent_file)
        return [row for row in self.session.execute(stmt).scalars().all()]

    def hybrid_search(
        self,
        query_text: str,
        query_embedding: list[float],
        fetch_n: int = 10,
        candidate_pool: int = 100,
        rrf_k: int = 60,
    ) -> list[dict]:
        sql = text("""
            WITH bm25 AS (
                SELECT id, content, parent_file,
                       ROW_NUMBER() OVER (ORDER BY paradedb.score(id) DESC) AS rank
                FROM document_chunks
                WHERE id @@@ paradedb.boolean(
                    should => ARRAY[
                        paradedb.match('content', :q),
                        paradedb.match('parent_file', :q)
                    ]
                )
                ORDER BY paradedb.score(id) DESC
                LIMIT :candidate_pool
            ),
            vec AS (
                SELECT id, content, parent_file,
                       ROW_NUMBER() OVER (ORDER BY embedding <=> :emb) AS rank
                FROM document_chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> :emb
                LIMIT :candidate_pool
            ),
            fused AS (
                SELECT
                    COALESCE(b.id, v.id) AS id,
                    COALESCE(b.content, v.content) AS content,
                    COALESCE(b.parent_file, v.parent_file) AS parent_file,
                    COALESCE(1.0 / (:rrf_k + b.rank), 0.0)
                  + COALESCE(1.0 / (:rrf_k + v.rank), 0.0) AS rrf_score
                FROM bm25 b
                FULL OUTER JOIN vec v ON b.id = v.id
            )
            SELECT id, content, parent_file, rrf_score
            FROM fused
            ORDER BY rrf_score DESC
            LIMIT :fetch_n
            """).bindparams(bindparam("emb", type_=Vector(DOC_EMBEDDING_DIM)))

        rows = (
            self.session.execute(
                sql,
                {
                    "q": query_text,
                    "emb": query_embedding,
                    "fetch_n": fetch_n,
                    "candidate_pool": candidate_pool,
                    "rrf_k": rrf_k,
                },
            )
            .mappings()
            .all()
        )

        return [dict(row) for row in rows]
