from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DiscoveredFile:
    filepath: Path
    extension: str
    size_bytes: int = 0


@dataclass
class IngestionSummary:
    files_discovered: int = 0
    files_failed: int = 0
    documents_loaded: int = 0
    chunks_created: int = 0
    num_added: int = 0
    num_updated: int = 0
    num_skipped: int = 0
    num_deleted: int = 0
    errors: list[str] = field(default_factory=list)

    def get_report(self) -> str:
        report = [
            f"\n✅ --- Ingestion Complete ---",
            f"Files Discovered : {self.files_discovered}",
            f"Files Failed     : {self.files_failed}",
            f"Raw Documents    : {self.documents_loaded}",
            f"Chunks Created   : {self.chunks_created}",
            f"{"-" * 26}",
            f"Chunks Added     : {self.num_added}",
            f"Chunks Updated   : {self.num_updated}",
            f"Chunks Skipped   : {self.num_skipped}",
            f"Chunks Deleted   : {self.num_deleted}",
        ]
        if self.errors:
            report.append(f"\n⚠️  {len(self.errors)} file(s) failed to load:")
            for err in self.errors:
                report.append(f"    - {err}")
        return "\n".join(report)


@dataclass
class SearchResult:
    content: str
    source: str
    score: float
