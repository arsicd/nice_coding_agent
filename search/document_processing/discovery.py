from pathlib import Path
from typing import Iterator

from lib.logger import get_logger
from search.entities import DiscoveredFile

SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt", ".docx"}

logger = get_logger(__name__)


def find_files(base_dir: Path) -> Iterator[DiscoveredFile]:
    if not base_dir.exists():
        logger.warning(f"Data directory does not exist: {base_dir}")
        return

    for path in base_dir.rglob("*"):
        if any(part.startswith(".") for part in path.parts):
            continue

        if path.is_file():
            ext = path.suffix.lower()
            if ext in SUPPORTED_EXTENSIONS:
                yield DiscoveredFile(
                    filepath=path,
                    extension=ext,
                    size_bytes=path.stat().st_size,
                )
