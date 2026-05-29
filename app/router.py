from abc import ABC, abstractmethod

from core import router as core_router
from core.container import AgentContainer
from core.schemas import CodeChangeResponse, ContextItem, PlanResponse, SearchResult


class IRouter(ABC):
    @abstractmethod
    async def build_context(self, instructions: str) -> list[ContextItem]: ...

    @abstractmethod
    async def plan_task(self, prompt: str) -> PlanResponse: ...

    @abstractmethod
    async def implement_task(self, prompt: str) -> CodeChangeResponse: ...

    @abstractmethod
    async def create_epic(self, instructions: str) -> str: ...

    @abstractmethod
    async def create_overview(self) -> str: ...

    @abstractmethod
    async def summarize_context_item(self, content: str, instructions: str) -> str: ...

    @abstractmethod
    async def ask_llm(self, question: str) -> str: ...

    @abstractmethod
    async def research(self, question: str) -> str: ...

    @abstractmethod
    async def browse(self, instruction: str) -> str: ...

    @abstractmethod
    async def web_search(self, query: str) -> str: ...

    @abstractmethod
    async def get_file_text(self, path: str) -> str: ...

    @abstractmethod
    async def get_ignore_list(self) -> list[str]: ...

    @abstractmethod
    async def create_file(self, path: str, content: str) -> None: ...

    @abstractmethod
    async def replace_text_in_file(
        self, path: str, old_text: str, new_text: str
    ) -> None: ...

    @abstractmethod
    async def list_directory_tree(self) -> str: ...

    @abstractmethod
    async def is_index_empty(self) -> bool: ...

    @abstractmethod
    async def run_ingestion(self) -> str: ...

    @abstractmethod
    async def search_documents(self, query: str, k: int = 4) -> list[SearchResult]: ...

    @abstractmethod
    async def set_model_mode(self, mode: str) -> None: ...

    @abstractmethod
    async def list_skills(self) -> list[str]: ...

    @abstractmethod
    async def get_skill_content(self, filename: str) -> str: ...

    @abstractmethod
    async def get_total_cost(self) -> float: ...

    @abstractmethod
    async def reset_cost(self) -> float: ...

    @abstractmethod
    async def get_model_mode(self) -> str: ...

    @abstractmethod
    async def cancel_llm_execution(self): ...

    @abstractmethod
    async def config_validation_errors(self) -> str | None: ...

    @abstractmethod
    async def get_settings_text(self) -> str: ...

    @abstractmethod
    async def save_settings_text(self, content: str) -> None: ...


class Router(IRouter):
    """Production Router that delegates to core.router functions."""

    def __init__(self, container: AgentContainer | None = None) -> None:
        self._container = container

    async def build_context(self, instructions: str) -> list[ContextItem]:
        return await core_router.build_context(instructions, self._container)

    async def plan_task(self, prompt: str) -> PlanResponse:
        return await core_router.plan_task(prompt, self._container)

    async def implement_task(self, prompt: str) -> CodeChangeResponse:
        return await core_router.implement_task(prompt, self._container)

    async def create_epic(self, instructions: str) -> str:
        return await core_router.create_epic(instructions, self._container)

    async def create_overview(self) -> str:
        return await core_router.create_overview(self._container)

    async def summarize_context_item(self, content: str, instructions: str) -> str:
        return await core_router.summarize_context_item(
            content, instructions, self._container
        )

    async def ask_llm(self, question: str) -> str:
        return await core_router.ask_llm(question, self._container)

    async def research(self, question: str) -> str:
        return await core_router.research(question, self._container)

    async def browse(self, instruction: str) -> str:
        return await core_router.browse(instruction, container=self._container)

    async def web_search(self, query: str) -> str:
        return await core_router.perform_web_search(query, self._container)

    async def get_file_text(self, path: str) -> str:
        return await core_router.get_file_text(path, self._container)

    async def get_ignore_list(self) -> list[str]:
        return await core_router.get_ignore_list()

    async def create_file(self, path: str, content: str) -> None:
        await core_router.create_file(path, content, self._container)

    async def replace_text_in_file(
        self, path: str, old_text: str, new_text: str
    ) -> None:
        await core_router.replace_text_in_file(
            path, old_text, new_text, self._container
        )

    async def list_directory_tree(self) -> str:
        return await core_router.list_directory_tree(self._container)

    async def is_index_empty(self) -> bool:
        return await core_router.is_index_empty()

    async def run_ingestion(self) -> str:
        return await core_router.run_ingestion(self._container)

    async def search_documents(self, query: str, k: int = 4) -> list[SearchResult]:
        return await core_router.search_documents(query, k, self._container)

    async def set_model_mode(self, mode: str) -> None:
        await core_router.set_model_mode(mode, self._container)

    async def list_skills(self) -> list[str]:
        return await core_router.list_skills()

    async def get_skill_content(self, filename: str) -> str:
        return await core_router.get_skill_content(filename)

    async def get_total_cost(self) -> float:
        return await core_router.get_total_cost()

    async def reset_cost(self) -> float:
        return await core_router.reset_cost()

    async def get_model_mode(self) -> str:
        return await core_router.get_model_mode()

    async def cancel_llm_execution(self):
        await core_router.cancel_llm_execution()

    async def config_validation_errors(self) -> str | None:
        return await core_router.config_validation_errors()

    async def get_settings_text(self) -> str:
        return await core_router.get_settings_text(self._container)

    async def save_settings_text(self, content: str) -> None:
        await core_router.save_settings_text(content, self._container)
