import logging
import sys


def _configure_root() -> None:
    root = logging.getLogger()
    if root.handlers:
        for h in root.handlers[:]:
            root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s", datefmt="%H:%M:%S"
        )
    )
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)

    for noisy in (
        "httpx",
        "httpcore",
        "uvicorn.access",
        "nicegui",
        "asyncio",
        "openai",
        "mcp",
        "watchfiles",
        "unstructured",
        "filelock",
        "MARKDOWN",
        "pypdf",
        "charset_normalizer",
        "sentence_transformers",
        "huggingface_hub",
        "chromadb",
        "urllib3.connectionpool",
        "sse_starlette.sse",
        # "root",
    ):
        logging.getLogger(noisy).setLevel(logging.WARNING)


_configure_root()


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
