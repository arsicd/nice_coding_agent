import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path

from search.ml_models import get_doc_embedder, release_embedder_cache
from search.db.database import new_session
from search.db.models import DocumentChunk
from search.document_processing.discovery import find_files
from search.document_processing.loaders import load_documents
from search.document_processing.splitters import split_documents
from search.db.repository import DocumentChunkRepository
from search.entities import DiscoveredFile
from lib.logger import get_logger

logger = get_logger(__name__)

BATCH_SIZE = 32


@dataclass
class DocumentIndexStats:
    indexed: int = 0
    skipped: int = 0
    emptied: int = 0
    failed: int = 0
    orphans_deleted: int = 0
    total_chunks: int = 0
    failed_paths: list[str] = field(default_factory=list)

    def get_report(self) -> str:
        report = [
            f"\n✅ --- Document Ingestion Complete ---",
            f"Files Indexed    : {self.indexed}",
            f"Files Skipped    : {self.skipped}",
            f"Files Emptied    : {self.emptied}",
            f"Files Failed     : {self.failed}",
            f"Orphans Deleted  : {self.orphans_deleted}",
            f"{'-' * 26}",
            f"Total Chunks     : {self.total_chunks}",
        ]
        if self.failed_paths:
            report.append(f"\n⚠️  {len(self.failed_paths)} file(s) failed to index:")
            for p in self.failed_paths:
                report.append(f"    - {p}")
        return "\n".join(report)


def _normalize_rel(p: str) -> str:
    norm = Path(p).as_posix()
    while norm.startswith("./"):
        norm = norm[2:]
    return norm.lstrip("/")


@dataclass
class _IndexResult:
    status: str  # "indexed" | "skipped" | "emptied"
    chunks: int


def _index_document_file(
    rel_path: str, base_dir: str, repo: DocumentChunkRepository
) -> _IndexResult:
    fs_path = os.path.join(base_dir, rel_path)
    h = hashlib.sha256()
    with open(fs_path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    content_hash = h.hexdigest()

    if repo.get_indexed_hash(rel_path) == content_hash:
        return _IndexResult(status="skipped", chunks=0)

    discovered = DiscoveredFile(
        filepath=Path(fs_path), extension=Path(fs_path).suffix.lower()
    )
    documents, errors = load_documents([discovered])

    if errors:
        raise RuntimeError(f"Failed to load document: {errors[0]}")

    if not documents:
        deleted = repo.delete_by_parent_file(rel_path)
        repo.upsert_indexed_document(rel_path, content_hash)
        if deleted:
            logger.info(f"Cleared {deleted} stale chunks for empty file {rel_path}")
        return _IndexResult(status="emptied", chunks=0)

    chunks = split_documents(documents)

    if not chunks:
        deleted = repo.delete_by_parent_file(rel_path)
        repo.upsert_indexed_document(rel_path, content_hash)
        if deleted:
            logger.info(f"Cleared {deleted} stale chunks for no-chunk file {rel_path}")
        return _IndexResult(status="emptied", chunks=0)

    deleted = repo.delete_by_parent_file(rel_path)

    texts = [c.page_content for c in chunks]
    total_chunks = len(chunks)

    for i in range(0, total_chunks, BATCH_SIZE):
        batch_chunks = chunks[i : i + BATCH_SIZE]
        batch_texts = texts[i : i + BATCH_SIZE]

        batch_embeddings = get_doc_embedder().embed_documents(batch_texts)

        batch_models = []
        for j, (chunk, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
            chunk_id = f"{rel_path}::doc::{i + j}"
            batch_models.append(
                DocumentChunk(
                    id=chunk_id,
                    parent_file=rel_path,
                    content=chunk.page_content,
                    embedding=embedding,
                )
            )

        repo.insert_chunks(batch_models)

    repo.upsert_indexed_document(rel_path, content_hash)

    logger.info(
        f"Indexed {total_chunks} chunks from {rel_path} "
        f"(replaced {deleted} existing)"
    )
    return _IndexResult(status="indexed", chunks=total_chunks)


def index_document_files(
    paths: list[str], base_dir: str, delete_orphans: bool = True
) -> DocumentIndexStats:
    stats = DocumentIndexStats()
    normalized = [_normalize_rel(p) for p in paths]

    session = new_session()
    repo = DocumentChunkRepository(session)

    try:
        for rel_path in normalized:
            try:
                result = _index_document_file(rel_path, base_dir, repo)
                session.commit()
            except Exception as e:
                session.rollback()
                logger.warning(f"Failed to index {rel_path}: {e}")
                stats.failed += 1
                stats.failed_paths.append(rel_path)
                continue

            if result.status == "indexed":
                stats.indexed += 1
                stats.total_chunks += result.chunks
                release_embedder_cache()
            elif result.status == "skipped":
                stats.skipped += 1
            elif result.status == "emptied":
                stats.emptied += 1

        if delete_orphans and not normalized:
            logger.warning(
                "No files supplied; skipping orphan deletion to prevent mass wipe"
            )
        elif delete_orphans:
            supplied = set(normalized)
            indexed_in_db = {_normalize_rel(p) for p in repo.list_indexed_documents()}
            orphans = indexed_in_db - supplied
            for orphan in orphans:
                try:
                    repo.delete_by_parent_file(orphan)
                    repo.delete_indexed_document(orphan)
                    session.commit()
                    stats.orphans_deleted += 1
                except Exception as e:
                    session.rollback()
                    logger.warning(f"Failed to delete orphan {orphan}: {e}")

        logger.info(
            f"Document indexing complete. indexed={stats.indexed} skipped={stats.skipped} "
            f"emptied={stats.emptied} failed={stats.failed} "
            f"orphans_deleted={stats.orphans_deleted} "
            f"total_chunks={stats.total_chunks}"
        )
    finally:
        session.close()

    return stats


def ingest_document_directory(target_path: str) -> DocumentIndexStats:
    base_dir = str(Path(target_path).resolve())

    discovered = list(find_files(Path(base_dir)))
    rel_paths: list[str] = []
    for file in discovered:
        rel_paths.append(os.path.relpath(str(file.filepath), base_dir))

    return index_document_files(rel_paths, base_dir, delete_orphans=True)
