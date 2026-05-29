from dataclasses import dataclass
import json
from pathlib import Path

import pathspec

from core.mcp_clients.filesystem.mcp_client_base import FilesystemMcpClient
from core.config import settings
from lib.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LocalFileSystemClient(FilesystemMcpClient):
    ignore_spec: pathspec.PathSpec | None = None

    def __post_init__(self):
        self.project_root = Path(str(settings.project_root)).resolve()
        self.agent_dir = self.project_root / ".nice"
        self.ignore_file = self.agent_dir / ".ignore"

    def _set_ignore_spec(self):
        with open(self.ignore_file, "r", encoding="utf-8") as f:
            self.ignore_spec = pathspec.PathSpec.from_lines("gitwildmatch", f)

    def _should_ignore(self, path: Path) -> bool:
        assert self.ignore_spec
        relative_path = str(path.relative_to(self.project_root))

        if path.is_dir():
            relative_path += "/"

        return self.ignore_spec.match_file(relative_path)

    async def get_file_text(self, path: str) -> str:
        target_path = self.project_root / path
        return target_path.read_text(encoding="utf-8")

    async def list_directory_tree(self) -> str:
        self._set_ignore_spec()

        tree_lines = [f"{self.project_root.name}/"]

        self._build_tree(tree_lines, self.project_root)

        ascii_tree = "\n".join(tree_lines) + "\n"
        result = {
            "traversedDirectory": str(self.project_root),
            "tree": ascii_tree,
            "errors": [],
        }

        return json.dumps(result, ensure_ascii=False)

    def _build_tree(self, tree_lines: list[str], current_path: Path, prefix: str = ""):
        try:
            raw_items = [
                item for item in current_path.iterdir() if not self._should_ignore(item)
            ]
            items = sorted(raw_items, key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return

        pointers = ["├── "] * (len(items) - 1) + ["└── "] if items else []

        for pointer, path in zip(pointers, items):
            if path.is_dir():
                tree_lines.append(f"{prefix}{pointer}{path.name}/")
                extension = "│   " if pointer == "├── " else "    "
                self._build_tree(tree_lines, path, prefix + extension)
            else:
                tree_lines.append(f"{prefix}{pointer}{path.name}")

    async def create_file(self, path: str, content: str) -> str:
        target_path = self.project_root / path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        return f"File created successfully at {path}"

    async def replace_text_in_file(
        self, path: str, old_text: str, new_text: str
    ) -> str:
        target_path = self.project_root / path
        content = target_path.read_text(encoding="utf-8")

        if old_text not in content:
            raise ValueError(f"Text not found in {path}")

        updated_content = content.replace(old_text, new_text, 1)
        target_path.write_text(updated_content, encoding="utf-8")
        return f"Text replaced successfully in {path}"
