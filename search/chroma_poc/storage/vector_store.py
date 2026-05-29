import threading

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from lib.logger import get_logger
from search.config import (
    EMBEDDING_MODEL,
    EMBEDDING_DEVICE,
    INDEX_NAME,
    CHROMA_PERSIST_DIR,
)

logger = get_logger(__name__)

_vector_store: Chroma | None = None
_lock = threading.Lock()


def get_vector_store() -> Chroma:
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    with _lock:
        logger.info(
            f"Loading embedding model '{EMBEDDING_MODEL}' on device '{EMBEDDING_DEVICE}' (first run may download ~440 MB)..."
        )

        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL, model_kwargs={"device": EMBEDDING_DEVICE}
        )

        _vector_store = Chroma(
            collection_name=INDEX_NAME,
            embedding_function=embeddings,
            persist_directory=str(CHROMA_PERSIST_DIR),
        )

        logger.info("ChromaDB initialized.")
        return _vector_store
