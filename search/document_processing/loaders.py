from typing import Iterable

from lib.logger import get_logger
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    Docx2txtLoader,
)

from search.entities import DiscoveredFile

logger = get_logger(__name__)

LOADER_MAPPING = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".md": UnstructuredMarkdownLoader,
    ".docx": Docx2txtLoader,
}


def load_documents(
    discovered_files: Iterable[DiscoveredFile],
) -> tuple[list[Document], list[str]]:
    documents: list[Document] = []
    errors: list[str] = []

    for file in discovered_files:
        loader_class = LOADER_MAPPING.get(file.extension)
        if not loader_class:
            logger.warning(
                f"No loader registered for extension '{file.extension}': {file.filepath}"
            )
            continue

        try:
            loader = loader_class(str(file.filepath))
            file_docs = list(loader.lazy_load())
            documents.extend(file_docs)
            logger.debug(f"Loaded {len(file_docs)} document(s) from {file.filepath}")
        except Exception as e:
            msg = f"{file.filepath}: {type(e).__name__}: {e}"
            logger.error(f"Failed to load {msg}")
            errors.append(msg)

    return documents, errors
