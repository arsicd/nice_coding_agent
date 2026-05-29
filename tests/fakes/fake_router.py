from dataclasses import dataclass, field

from app.router import IRouter
from core.schemas import CodeChangeResponse, ContextItem, PlanResponse, SearchResult


@dataclass
class FakeRouter(IRouter):
    """Test double for Router. Each method returns a configurable canned value
    and records the call for assertions."""

    calls: list[tuple[str, tuple, dict]] = field(default_factory=list)
    build_context_result: list[ContextItem] = field(default_factory=list)
    plan_task_result: PlanResponse = field(
        default_factory=lambda: PlanResponse(summary="")
    )
    implement_task_result: CodeChangeResponse = field(
        default_factory=lambda: CodeChangeResponse(summary="")
    )
    create_epic_result: str = ""
    create_overview_result: str = ""
    summarize_result: str = ""
    ask_llm_result: str = ""
    research_result: str = ""
    browse_result: str = ""
    web_search_result: str = ""
    file_text_result: str = ""
    directory_tree_result: str = ""
    ingestion_result: str = ""
    search_documents_result: list[SearchResult] = field(default_factory=list)
    skills_result: list[str] = field(default_factory=list)
    skill_content_result: str = ""
    total_cost: float = 0.0
    model_mode: str = "standard"

    def _record(self, name: str, *args, **kwargs) -> None:
        self.calls.append((name, args, kwargs))

    async def build_context(self, instructions: str) -> list[ContextItem]:
        self._record("build_context", instructions)
        return list(self.build_context_result)

    async def plan_task(self, prompt: str) -> PlanResponse:
        self._record("plan_task", prompt)
        return self.plan_task_result

    async def implement_task(self, prompt: str) -> CodeChangeResponse:
        self._record("implement_task", prompt)
        return self.implement_task_result

    async def create_epic(self, instructions: str) -> str:
        self._record("create_epic", instructions)
        return self.create_epic_result

    async def create_overview(self) -> str:
        self._record("create_overview")
        return self.create_overview_result

    async def summarize_context_item(self, content: str, instructions: str) -> str:
        self._record("summarize_context_item", content, instructions)
        return self.summarize_result

    async def ask_llm(self, question: str) -> str:
        self._record("ask_llm", question)
        return self.ask_llm_result

    async def research(self, question: str) -> str:
        self._record("research", question)
        return self.research_result

    async def browse(self, instruction: str) -> str:
        self._record("browse", instruction)
        return self.browse_result

    async def web_search(self, query: str) -> str:
        self._record("web_search", query)
        return self.web_search_result

    async def get_file_text(self, path: str) -> str:
        self._record("get_file_text", path)
        return self.file_text_result

    async def create_file(self, path: str, content: str) -> None:
        self._record("create_file", path, content)

    async def replace_text_in_file(
        self, path: str, old_text: str, new_text: str
    ) -> None:
        self._record("replace_text_in_file", path, old_text, new_text)

    async def list_directory_tree(self) -> str:
        self._record("list_directory_tree")
        return self.directory_tree_result

    async def run_ingestion(self) -> str:
        self._record("run_ingestion")
        return self.ingestion_result

    async def search_documents(self, query: str, k: int = 4) -> list[SearchResult]:
        self._record("search_documents", query, k)
        return list(self.search_documents_result)

    async def set_model_mode(self, mode: str) -> None:
        self._record("set_model_mode", mode)

    async def list_skills(self) -> list[str]:
        self._record("list_skills")
        return list(self.skills_result)

    async def get_skill_content(self, filename: str) -> str:
        self._record("get_skill_content", filename)
        return self.skill_content_result

    async def get_total_cost(self) -> float:
        return self.total_cost

    async def reset_cost(self):
        self.total_cost = 0.0

    async def get_model_mode(self) -> str:
        return self.model_mode

    async def get_ignore_list(self) -> list[str]:
        return [".env"]

    async def is_index_empty(self) -> bool:
        return False

    async def cancel_llm_execution(self):
        self._record("cancel_llm_execution")
