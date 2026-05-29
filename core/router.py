import asyncio

from core.workflows.build_context import main as main_build_context
from core.workflows.plan_task import main as main_plan_task
from core.workflows.implement_task import main as main_implement_task
from core.workflows.create_overview import main as main_create_overview
from core.workflows.create_epic import main as main_create_epic
from core.workflows.summarize_item import main as main_summarize_item
from core.workflows.ask_llm import main as main_ask_llm
from core.workflows.research import main as main_research
from core.workflows.browse import main as main_browse
from core.container import AgentContainer, get_container
from core.schemas import CodeChangeResponse, PlanResponse, SearchResult, ContextItem
from core.agent_tools import list_skills_tool, get_skill_content_tool
from core.config import settings, reload_settings
from search.document_indexer import ingest_document_directory
from search.document_search import hybrid_document_search
from search.db.database import ensure_schema_migrated

ENV_FILE = ".nice/.env"


async def build_context(
    instructions: str, container: AgentContainer | None = None
) -> list[ContextItem]:
    return await main_build_context(instructions, container)


async def plan_task(
    prompt: str, container: AgentContainer | None = None
) -> PlanResponse:
    return await main_plan_task(prompt, container)


async def implement_task(
    prompt: str, container: AgentContainer | None = None
) -> CodeChangeResponse:
    return await main_implement_task(prompt, container)


async def create_epic(
    instructions: str, container: AgentContainer | None = None
) -> str:
    return await main_create_epic(instructions, container)


async def create_overview(container: AgentContainer | None = None) -> str:
    return await main_create_overview(container)


async def summarize_context_item(
    content: str, instructions: str, container: AgentContainer | None = None
) -> str:
    return await main_summarize_item(content, instructions, container)


async def ask_llm(question: str, container: AgentContainer | None = None) -> str:
    return await main_ask_llm(question, container)


async def research(question: str, container: AgentContainer | None = None) -> str:
    return await main_research(question, container)


async def browse(
    instruction: str, headless: bool = False, container: AgentContainer | None = None
) -> str:
    return await main_browse(instruction, headless, container)


async def perform_web_search(
    query: str, container: AgentContainer | None = None
) -> str:
    resolved = container or get_container()
    results = await resolved.web_search.web_search(query, 2, 1000)
    return await main_summarize_item(str(results), query, resolved)


async def get_file_text(path: str, container: AgentContainer | None = None):
    resolved = container or get_container()
    return await resolved.mcp_client.get_file_text(path=path)


async def get_ignore_list(container: AgentContainer | None = None):
    resolved = container or get_container()
    return await resolved.get_ignore_list()


async def create_file(path: str, content: str, container: AgentContainer | None = None):
    resolved = container or get_container()
    await resolved.mcp_client.create_file(path=path, content=content)


async def replace_text_in_file(
    path: str, old_text: str, new_text: str, container: AgentContainer | None = None
):
    resolved = container or get_container()
    await resolved.mcp_client.replace_text_in_file(
        path=path, old_text=old_text, new_text=new_text
    )


async def list_directory_tree(container: AgentContainer | None = None):
    resolved = container or get_container()
    return await resolved.mcp_client.list_directory_tree()


async def is_index_empty(container: AgentContainer | None = None):
    resolved = container or get_container()
    return resolved.overview_cache.is_empty()


async def run_ingestion(container: AgentContainer | None = None) -> str:
    resolved = container or get_container()
    stats = await asyncio.to_thread(
        ingest_document_directory, str(settings.project_root / "documents")
    )
    return stats.get_report()


async def search_documents(
    query: str, k: int = 4, container: AgentContainer | None = None
) -> list[SearchResult]:
    resolved = container or get_container()
    results = await asyncio.to_thread(
        hybrid_document_search, query, fetch_n=20, top_n=k
    )
    return [
        SearchResult(
            content=r["content"],
            source=r["parent_file"],
            score=r["rerank_score"],
        )
        for r in results
    ]


async def set_model_mode(mode: str, container: AgentContainer | None = None):
    resolved = container or get_container()
    resolved.set_model_mode(mode)  # type: ignore[arg-type]


async def list_skills():
    return await list_skills_tool()


async def get_skill_content(filename: str):
    return await get_skill_content_tool(filename)


async def get_total_cost(container: AgentContainer | None = None) -> float:
    resolved = container or get_container()
    return resolved.cost_tracker.total_cost


async def reset_cost(container: AgentContainer | None = None) -> float:
    resolved = container or get_container()
    return resolved.cost_tracker.reset()


async def get_model_mode(container: AgentContainer | None = None) -> str:
    resolved = container or get_container()
    return resolved.model_mode


async def cancel_llm_execution(container: AgentContainer | None = None):
    resolved = container or get_container()
    resolved.cancel = True


async def config_validation_errors(_: AgentContainer | None = None) -> str | None:
    return settings.validation_errors()


async def get_settings_text(container: AgentContainer | None = None) -> str:
    resolved = container or get_container()
    return await resolved.mcp_client.get_file_text(ENV_FILE)


async def save_settings_text(
    content: str, container: AgentContainer | None = None
) -> None:
    resolved = container or get_container()
    await resolved.mcp_client.create_file(ENV_FILE, content)
    reload_settings()
    resolved.invalidate_llm_cache()
    resolved.set_web_search()
    if not settings.validation_errors():
        ensure_schema_migrated()
