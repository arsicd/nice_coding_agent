from abc import ABC, abstractmethod
from functools import lru_cache

from mxbai_rerank import MxbaiRerankV2
from sentence_transformers import SentenceTransformer
from sentence_transformers import CrossEncoder
import torch

from search.config import (
    ACTIVE_CODE_EMBEDDER,
    ACTIVE_DOC_EMBEDDER,
    ACTIVE_RERANKER,
    EMBEDDING_DEVICE,
)
from lib.logger import get_logger

logger = get_logger(__name__)


if EMBEDDING_DEVICE == "mps":
    _ST_BACKEND_KWARGS = {"device": "mps"}
    _CE_BACKEND_KWARGS = {"device": "mps"}
elif EMBEDDING_DEVICE == "cpu":
    _ST_BACKEND_KWARGS = {
        "backend": "onnx",
        "model_kwargs": {
            "file_name": "onnx/model_quantized.onnx",
            "provider": "CPUExecutionProvider",
        },
    }
    _CE_BACKEND_KWARGS = {
        "backend": "onnx",
        "model_kwargs": {
            "file_name": "onnx/model_quantized.onnx",
            "provider": "CPUExecutionProvider",
        },
    }
else:
    raise NotImplementedError(f"Unknown embedding device: {EMBEDDING_DEVICE}")


class Embedder(ABC):
    # Declared dim — committed to the DB schema. Must match the loaded model's
    # actual dim; checked in each subclass's __init__.
    DIM: int

    @property
    @abstractmethod
    def dim(self) -> int:
        """Embedding dimension reported by the loaded model."""

    @abstractmethod
    def embed_queries(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...


class Reranker(ABC):
    @abstractmethod
    def score(self, query: str, documents: list[str]) -> list[float]:
        """Score per document, aligned with input order. Higher = more relevant."""


class JinaCodeEmbedder(Embedder):
    MODEL_NAME = "jinaai/jina-embeddings-v2-base-code"
    DIM = 768
    BATCH_SIZE = 8
    MAX_SEQ_LENGTH = 1024  # Tail-truncate chunks, performance reasons

    def __init__(self) -> None:
        logger.info(f"Loading embedder: {self.MODEL_NAME}")
        self._model = SentenceTransformer(
            self.MODEL_NAME, trust_remote_code=True, **_ST_BACKEND_KWARGS
        )
        self._model.max_seq_length = self.MAX_SEQ_LENGTH
        if self.dim != self.DIM:
            raise RuntimeError(
                f"Embedding dim mismatch for {self.MODEL_NAME}: "
                f"model reports {self.dim}, class declares {self.DIM}"
            )
        logger.info(f"Embedder loaded (dim={self.dim})")

    @property
    def dim(self) -> int:
        return self._model.get_embedding_dimension()

    def _encode(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(
            texts,
            batch_size=self.BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).tolist()

    # Jina v2 code is symmetric — no query/document prefix asymmetry.
    def embed_queries(self, texts: list[str]) -> list[list[float]]:
        return self._encode(texts)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._encode(texts)


class NomicV15Embedder(Embedder):
    MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"
    # Native dim is 768; truncated via Matryoshka Representation Learning to
    # 256 for ~3x storage savings with negligible quality loss.
    DIM = 256
    BATCH_SIZE = 32
    MAX_SEQ_LENGTH = 1024  # Tail-truncate chunks, performance reasons

    _QUERY_PREFIX = "search_query: "
    _DOC_PREFIX = "search_document: "

    def __init__(self) -> None:
        logger.info(f"Loading embedder: {self.MODEL_NAME} (MRL→{self.DIM})")
        self._model = SentenceTransformer(
            self.MODEL_NAME,
            trust_remote_code=True,
            truncate_dim=self.DIM,
            **_ST_BACKEND_KWARGS,
        )
        self._model.max_seq_length = self.MAX_SEQ_LENGTH
        if self.dim != self.DIM:
            raise RuntimeError(
                f"Embedding dim mismatch for {self.MODEL_NAME}: "
                f"model reports {self.dim}, class declares {self.DIM}"
            )
        logger.info(f"Embedder loaded (dim={self.dim})")

    @property
    def dim(self) -> int:
        return self._model.get_embedding_dimension()

    def _encode(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(
            texts,
            batch_size=self.BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).tolist()

    def embed_queries(self, texts: list[str]) -> list[list[float]]:
        return self._encode([self._QUERY_PREFIX + t for t in texts])

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._encode([self._DOC_PREFIX + t for t in texts])


class JinaRerankerV2(Reranker):
    MODEL_NAME = "jinaai/jina-reranker-v2-base-multilingual"

    def __init__(self) -> None:
        logger.info(f"Loading reranker: {self.MODEL_NAME}")
        self._model = CrossEncoder(
            self.MODEL_NAME,
            max_length=1024,
            trust_remote_code=True,
            **_CE_BACKEND_KWARGS,
        )
        logger.info("Reranker loaded")

    def score(self, query: str, documents: list[str]) -> list[float]:
        scores = self._model.predict([[query, d] for d in documents])
        return [float(s) for s in scores]


class MxbaiRerankerV2(Reranker):
    MODEL_NAME = "mixedbread-ai/mxbai-rerank-base-v2"

    def __init__(self) -> None:
        logger.info(f"Loading reranker: {self.MODEL_NAME}")
        self._model = MxbaiRerankV2(self.MODEL_NAME, max_length=8192)
        logger.info("Reranker loaded")

    def score(self, query: str, documents: list[str]) -> list[float]:
        # mxbai.rank() returns results sorted by relevance — remap to input order.
        # Pass top_k explicitly: default behavior varies by mxbai-rerank version
        # and a silent top_k truncation would leave un-scored docs with sentinel
        # values, corrupting the final ranking.
        results = self._model.rank(
            query=query,
            documents=documents,
            top_k=len(documents),
            return_documents=False,
        )
        if len(results) != len(documents):
            raise RuntimeError(
                f"mxbai reranker returned {len(results)} scores for "
                f"{len(documents)} documents — refusing to fabricate the rest"
            )
        scores: list[float | None] = [None] * len(documents)
        for r in results:
            scores[r.index] = float(r.score)
        if any(s is None for s in scores):
            missing = [i for i, s in enumerate(scores) if s is None]
            raise RuntimeError(
                f"mxbai reranker did not score documents at indices {missing}"
            )
        return scores  # type: ignore[return-value]


EMBEDDERS: dict[str, type[Embedder]] = {
    "jina-code": JinaCodeEmbedder,
    "nomic-v1.5": NomicV15Embedder,
}

RERANKERS: dict[str, type[Reranker]] = {
    "jina-v2": JinaRerankerV2,
    "mxbai-v2": MxbaiRerankerV2,
}

CODE_EMBEDDING_DIM = EMBEDDERS[ACTIVE_CODE_EMBEDDER].DIM
DOC_EMBEDDING_DIM = EMBEDDERS[ACTIVE_DOC_EMBEDDER].DIM


@lru_cache(maxsize=1)
def get_code_embedder() -> Embedder:
    return EMBEDDERS[ACTIVE_CODE_EMBEDDER]()


@lru_cache(maxsize=1)
def get_doc_embedder() -> Embedder:
    return EMBEDDERS[ACTIVE_DOC_EMBEDDER]()


@lru_cache(maxsize=1)
def get_reranker() -> Reranker:
    return RERANKERS[ACTIVE_RERANKER]()


def release_embedder_cache() -> None:
    if EMBEDDING_DEVICE == "mps":
        torch.mps.empty_cache()


def warmup_code() -> None:
    get_code_embedder()
    get_reranker()


def warmup_documents() -> None:
    get_doc_embedder()
    get_reranker()


def warmup() -> None:
    get_code_embedder()
    get_doc_embedder()
    get_reranker()
