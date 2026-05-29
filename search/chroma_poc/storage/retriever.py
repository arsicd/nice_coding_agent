from lib.logger import get_logger
from search.chroma_poc.storage.vector_store import get_vector_store
from search.entities import SearchResult

logger = get_logger(__name__)


def search_documents(query: str, k: int = 4) -> list[SearchResult]:
    vector_store = get_vector_store()
    results = vector_store.similarity_search_with_score(query, k=k)

    output = []
    for doc, score in results:
        output.append(
            SearchResult(
                doc.page_content, doc.metadata.get("source", "unknown"), float(score)
            )
        )

    logger.info(f"Search for '{query}' returned {len(output)} result(s).")
    return output
