from core.config import settings

ROOT_DIR = settings.project_root
DATA_DIR = ROOT_DIR / "documents"

CHUNK_SIZE = settings.chunk_size
CHUNK_OVERLAP = settings.chunk_overlap

ACTIVE_CODE_EMBEDDER = settings.code_embedder
ACTIVE_DOC_EMBEDDER = settings.doc_embedder
ACTIVE_RERANKER = settings.reranker
EMBEDDING_DEVICE = settings.embedding_device
