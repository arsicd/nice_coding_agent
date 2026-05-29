from search.db.database import new_session
from search.db.repository import CodeChunkRepository
from search.ml_models import get_code_embedder, get_reranker
from lib.logger import get_logger

logger = get_logger(__name__)


def hybrid_search(
    query: str,
    fetch_n: int = 10,
    top_n: int = 3,
) -> list[dict]:
    """
    Two-stage retrieval:
      1. Postgres CTE fuses BM25 and pgvector ANN via Reciprocal Rank Fusion,
         returning up to fetch_n candidates.
      2. Cross-encoder rescores (query, content) pairs for the final ordering,
         and we return the top_n.

    Returns a list of dicts with the chunk row plus a cross_encoder_score.
    """
    query_embedding = get_code_embedder().embed_queries([query])[0]

    session = new_session()
    try:
        repo = CodeChunkRepository(session)
        candidates = repo.hybrid_search(
            query_text=query,
            query_embedding=query_embedding,
            fetch_n=fetch_n,
        )
    finally:
        session.close()

    if not candidates:
        return []

    scores = get_reranker().score(query, [c["content"] for c in candidates])

    for c, s in zip(candidates, scores):
        c["rerank_score"] = s

    candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
    return candidates[:top_n]
