from typing import Any

from lib.logger import get_logger
from langchain_core.documents import Document
from langchain_classic.indexes import SQLRecordManager
from langchain_core.indexing import index
from langchain_chroma import Chroma

from search.config import (
    INDEX_NAME,
    RECORD_MANAGER_DB_URL,
    INDEXING_CLEANUP_MODE,
)

logger = get_logger(__name__)


def index_documents(chunks: list[Document], vector_store: Chroma) -> dict[str, Any]:
    namespace = f"chroma/{INDEX_NAME}"

    record_manager = SQLRecordManager(
        namespace,
        db_url=RECORD_MANAGER_DB_URL,
    )

    record_manager.create_schema()

    result = index(
        docs_source=chunks,
        record_manager=record_manager,
        vector_store=vector_store,
        cleanup=INDEXING_CLEANUP_MODE,
        source_id_key="source",
        key_encoder="blake2b",
    )

    logger.info(f"Index result: {result}")
    return result
