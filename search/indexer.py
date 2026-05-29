import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path

from search.ml_models import get_code_embedder
from search.db.database import new_session
from search.db.models import CodeChunk
from search.db.repository import CodeChunkRepository
from lib.logger import get_logger
from lib.treesitter_extractor import (
    LANGUAGES,
    chunk_file_content,
    extract_signatures_from_content,
)

logger = get_logger(__name__)

IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "build", "dist"}


@dataclass
class IndexStats:
    indexed: int = 0
    skipped: int = 0
    emptied: int = 0
    failed: int = 0
    orphans_deleted: int = 0
    total_chunks: int = 0

    failed_paths: list[str] = field(default_factory=list)


def _normalize_rel(p: str) -> str:
    """
    Canonical form for project-relative paths used as identifiers.
    Forward slashes, no leading './' or '/'. Stable across OSes.
    """
    norm = Path(p).as_posix()
    while norm.startswith("./"):
        norm = norm[2:]
    return norm.lstrip("/")


def index_files(
    paths: list[str], base_dir: str, delete_orphans: bool = True
) -> IndexStats:
    stats = IndexStats()
    normalized = [_normalize_rel(p) for p in paths]

    session = new_session()
    repo = CodeChunkRepository(session)

    try:
        for rel_path in normalized:
            if Path(rel_path).suffix not in LANGUAGES:
                continue
            try:
                result = _index_file(rel_path, base_dir, repo)
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
            indexed_in_db = {_normalize_rel(p) for p in repo.list_indexed_files()}
            orphans = indexed_in_db - supplied
            for orphan in orphans:
                try:
                    repo.delete_by_parent_file(orphan)
                    repo.delete_indexed_file(orphan)
                    session.commit()
                    stats.orphans_deleted += 1
                except Exception as e:
                    session.rollback()
                    logger.warning(f"Failed to delete orphan {orphan}: {e}")

        logger.info(
            f"Indexing complete. indexed={stats.indexed} skipped={stats.skipped} "
            f"emptied={stats.emptied} failed={stats.failed} "
            f"orphans_deleted={stats.orphans_deleted} "
            f"total_chunks={stats.total_chunks}"
        )
    finally:
        session.close()

    return stats


def ingest_directory(target_path: str) -> IndexStats:
    base_dir = str(Path(target_path).resolve())
    rel_paths: list[str] = []
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            if Path(file).suffix in LANGUAGES:
                abs_path = os.path.join(root, file)
                rel_paths.append(os.path.relpath(abs_path, base_dir))

    return index_files(rel_paths, base_dir, delete_orphans=True)


@dataclass
class _IndexResult:
    status: str  # "indexed" | "skipped" | "emptied"
    chunks: int


def _index_file(
    rel_path: str, base_dir: str, repo: CodeChunkRepository
) -> _IndexResult:
    fs_path = os.path.join(base_dir, rel_path)
    with open(fs_path, "r", encoding="utf-8") as f:
        content = f.read()

    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    if repo.get_indexed_hash(rel_path) == content_hash:
        return _IndexResult(status="skipped", chunks=0)

    signatures = extract_signatures_from_content(rel_path, content)
    chunks = chunk_file_content(rel_path, content)

    if not chunks:
        deleted = repo.delete_by_parent_file(rel_path)
        repo.upsert_indexed_file(rel_path, content_hash)
        if deleted:
            logger.info(f"Cleared {deleted} stale chunks for empty file {rel_path}")
        return _IndexResult(status="emptied", chunks=0)

    embeddings = get_code_embedder().embed_documents([c["content"] for c in chunks])
    models = _build_chunk_models(rel_path, chunks, signatures, embeddings)

    deleted = repo.delete_by_parent_file(rel_path)
    repo.insert_chunks(models)
    repo.upsert_indexed_file(rel_path, content_hash)

    logger.info(
        f"Indexed {len(models)} chunks from {rel_path} "
        f"(replaced {deleted} existing)"
    )
    return _IndexResult(status="indexed", chunks=len(models))


def _build_chunk_models(
    file_path: str,
    chunks: list[dict],
    signatures: str,
    embeddings: list[list[float]],
) -> list[CodeChunk]:
    models = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_id = f"{file_path}::{chunk['type']}::{chunk['name']}::{i}"
        models.append(
            CodeChunk(
                id=chunk_id,
                parent_file=file_path,
                chunk_type=chunk["type"],
                chunk_name=chunk["name"],
                content=chunk["content"],
                file_signatures=signatures or None,
                embedding=embedding,
            )
        )
    return models
