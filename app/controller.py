from dataclasses import dataclass

from lib.logger import get_logger
from core.schemas import (
    CodeChange,
    CodeChangeResponse,
    PlanResponse,
    SearchResult,
    ContextItem,
)
from lib.tree_parser import parse_tree_to_nodes
from app.router import IRouter
from app.state import AppState
from app.exceptions import (
    AgentError,
    DirectoryTreeError,
    EmptyContextError,
    FileReadError,
)

logger = get_logger(__name__)


@dataclass
class AppController:
    state: AppState
    _router: IRouter

    async def set_model_mode(self, mode: str) -> None:
        await self._router.set_model_mode(mode)

    async def implement_task(self) -> CodeChangeResponse:
        await self.reload_context_files()
        context_text = self.state.build_llm_prompt()
        if not context_text:
            raise EmptyContextError()
        try:
            return await self._router.implement_task(context_text)
        except EmptyContextError:
            raise
        except Exception as exc:
            raise AgentError(f"LLM agent failed: {exc}") from exc

    async def plan_task(self) -> PlanResponse:
        await self.reload_context_files()
        context_text = self.state.build_llm_prompt()
        if not context_text:
            raise EmptyContextError()
        try:
            return await self._router.plan_task(context_text)
        except EmptyContextError:
            raise
        except Exception as exc:
            raise AgentError(f"LLM agent failed: {exc}") from exc

    async def apply_code_change(self, change: CodeChange) -> None:
        try:
            if change.is_new_file:
                await self._router.create_file(
                    path=change.file_path, content=change.new_text
                )
            else:
                await self._router.replace_text_in_file(
                    path=change.file_path,
                    old_text=change.old_text,
                    new_text=change.new_text,
                )
        except Exception as exc:
            raise AgentError(
                f"Failed to apply change to {change.file_path}: {exc}"
            ) from exc

    async def summarize_context_item(self, entry_id: str) -> str:
        content = next(
            (
                e.raw_content or e.content
                for e in self.state.context_entries
                if e.id == entry_id
            ),
            "",
        )
        instructions = self.state.instructions
        if not content:
            raise ValueError("No content found for entry")
        return await self._router.summarize_context_item(content, instructions)

    async def run_documents_ingestion(self) -> str:
        return await self._router.run_ingestion()

    async def search_documents(self, query: str, k: int = 4) -> list[SearchResult]:
        return await self._router.search_documents(query, k)

    async def web_search(self, query: str) -> str:
        return await self._router.web_search(query)

    async def ask_llm(self, question: str) -> str:
        try:
            return await self._router.ask_llm(question)
        except Exception as exc:
            raise AgentError(f"LLM question failed: {exc}") from exc

    async def research(self, question: str) -> str:
        try:
            return await self._router.research(question)
        except Exception as exc:
            raise AgentError(f"Research failed: {exc}") from exc

    async def browse(self, instruction: str) -> str:
        try:
            return await self._router.browse(instruction)
        except Exception as exc:
            raise AgentError(f"Browsing failed: {exc}") from exc

    async def list_skills(self) -> list[str]:
        return await self._router.list_skills()

    async def get_skill_content(self, filename: str) -> str:
        return await self._router.get_skill_content(filename)

    async def get_total_cost(self) -> float:
        return await self._router.get_total_cost()

    async def build_context(self) -> list[ContextItem]:
        try:
            return await self._router.build_context(self.state.instructions)
        except Exception as exc:
            raise AgentError(f"LLM agent failed: {exc}") from exc

    async def create_overview(self) -> str:
        return await self._router.create_overview()

    async def create_epic(self, instructions: str) -> str:
        return await self._router.create_epic(instructions)

    async def load_file_tree(self) -> None:
        try:
            raw = await self._router.list_directory_tree()
        except Exception as exc:
            raise DirectoryTreeError(f"Could not load directory tree: {exc}") from exc
        self.state.tree_nodes = parse_tree_to_nodes(raw)
        self.state.tree_loaded = True

    async def is_index_empty(self) -> bool:
        return await self._router.is_index_empty()

    async def fetch_file_content(self, node_id: str) -> str:
        try:
            return await self._router.get_file_text(node_id)
        except Exception as exc:
            raise FileReadError(path=node_id, cause=exc) from exc

    def collect_files_under_folder(self, folder_path: str) -> list[str]:
        """Recursively collect all file paths under a folder from the loaded tree."""
        file_paths: list[str] = []

        def _traverse(nodes: list[dict]) -> None:
            for node in nodes:
                if node.get("icon") == "folder":
                    _traverse(node.get("children") or [])
                else:
                    file_paths.append(node["id"])

        folder_node = self.get_tree_node(folder_path)
        if folder_node:
            children = folder_node.get("children") or []
            _traverse(children)

        return file_paths

    def get_tree_node(self, node_id: str) -> dict | None:
        def _search(nodes: list[dict]) -> dict | None:
            for node in nodes:
                if node["id"] == node_id:
                    return node
                children = node.get("children") or []
                result = _search(children)
                if result:
                    return result
            return None

        return _search(self.state.tree_nodes)

    def format_tree_as_text(self) -> str:
        """Format the loaded tree nodes as an indented text tree for LLM consumption."""
        lines: list[str] = []

        def _walk(nodes: list[dict], indent: int = 0) -> None:
            for node in nodes:
                prefix = "  " * indent
                lines.append(f"{prefix}{node['label']}")
                if node.get("is_folder") and node.get("children"):
                    _walk(node["children"], indent + 1)

        _walk(self.state.tree_nodes)
        return "\n".join(lines)

    async def reload_context_files(self) -> None:
        """Reload raw_content and rendered content for file entries before sending context to LLM."""
        for entry in self.state.context_entries:
            if entry.is_file_entry():
                path = entry.file_path_from_label()
                try:
                    raw = await self.fetch_file_content(path)
                    ext = entry.file_extension()
                    content = f"```{ext}\n{raw}\n```"
                    self.state.update_context_entry(
                        entry_id=entry.id,
                        content=entry.file_content_md(content),
                        raw_content=raw,
                        is_minimized=entry.is_minimized,
                    )
                except Exception as exc:
                    logger.warning(f"Failed to reload {path}: {exc}")

    async def reset_cost(self):
        await self._router.reset_cost()

    async def sync_model_mode(self):
        mode = await self._router.get_model_mode()
        self.state.set_model_mode(mode)

    async def cancel_llm_execution(self) -> None:
        await self._router.cancel_llm_execution()

    async def config_validation_errors(self) -> str | None:
        return await self._router.config_validation_errors()

    async def get_settings_text(self) -> str:
        return await self._router.get_settings_text()

    async def save_settings_text(self, content: str) -> None:
        await self._router.save_settings_text(content)
