import sys

from lib.logger import get_logger
from search.config import (
    DATA_DIR,
    DB_FILES_DIR,
    CHROMA_PERSIST_DIR,
    INDEXING_CLEANUP_MODE,
)
from search.entities import IngestionSummary
from search.document_processing.discovery import find_files
from search.document_processing.loaders import load_documents
from search.document_processing.splitters import split_documents
from search.chroma_poc.storage.vector_store import get_vector_store
from search.chroma_poc.storage.indexer import index_documents

logger = get_logger(__name__)


def setup_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_FILES_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)


def run() -> IngestionSummary:
    logger.info("🚀 Starting local RAG ingestion pipeline...")
    setup_directories()
    summary = IngestionSummary()

    # ── Step 1: Fail fast — validate storage before expensive work ────────────
    logger.info("\n🧠 Initializing embeddings and vector store...")
    vector_store = get_vector_store()

    # ── Step 2: Discover files ────────────────────────────────────────────────
    logger.info(f"\n📁 Scanning {DATA_DIR} for supported files...")
    discovered_files = list(find_files(DATA_DIR))
    summary.files_discovered = len(discovered_files)
    logger.info(f"   Found {summary.files_discovered} file(s).")

    if summary.files_discovered == 0:
        logger.info(
            "\n⚠️  No supported files found. Add PDFs, MDs, TXTs, or DOCXs to the data/ folder."
        )
        return summary

    # ── Step 3: Load documents ────────────────────────────────────────────────
    logger.info("\n📄 Loading documents...")
    documents, load_errors = load_documents(discovered_files)
    summary.documents_loaded = len(documents)
    summary.files_failed = len(load_errors)
    summary.errors = load_errors
    logger.info(f"   Loaded {summary.documents_loaded} raw page(s) / document(s).")
    if load_errors:
        logger.error(
            f"   ⚠️  {summary.files_failed} file(s) failed to load (see report)."
        )

    if not documents:
        logger.error("\n❌ No documents could be loaded. Aborting.")
        return summary

    # ── Step 4: Split into chunks ─────────────────────────────────────────────
    logger.info("\n✂️  Chunking documents...")
    chunks = split_documents(documents)
    summary.chunks_created = len(chunks)
    logger.info(f"   Created {summary.chunks_created} chunk(s).")

    # ── Step 5: Index / sync ──────────────────────────────────────────────────
    logger.info(f"\n🔄 Indexing chunks (cleanup mode: '{INDEXING_CLEANUP_MODE}')...")
    index_result = index_documents(chunks, vector_store)

    summary.num_added = index_result.get("num_added", 0)
    summary.num_updated = index_result.get("num_updated", 0)
    summary.num_skipped = index_result.get("num_skipped", 0)
    summary.num_deleted = index_result.get("num_deleted", 0)

    # ── Step 6: Report ────────────────────────────────────────────────────────
    report = summary.get_report()
    logger.info(report)
    return summary


if __name__ == "__main__":
    run()
