from pathlib import Path
from functools import lru_cache

from core.agent_tools import ToolName
from core.config import settings

_PROMPTS_DIR = Path(__file__).parent / "prompts"


@lru_cache(maxsize=None)
def get_prompt(name: str) -> str:
    path = _PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def get_build_context_prompt() -> str:
    allowed_tools = [
        ToolName.INVESTIGATE_FILE,
        ToolName.SEARCH_CODE,
        ToolName.WEB_SEARCH,
        ToolName.GET_SKILL_CONTENT,
        ToolName.INCLUDE_IN_CONTEXT,
        ToolName.EXCLUDE_FROM_CONTEXT,
    ]
    rag_rule = ""

    if settings.use_rag:
        allowed_tools.append(ToolName.SEARCH_LOCAL_DOCUMENTS)
        rag_rule = "Use `search_local_documents` for indexed project docs, PDFs, notes, or internal knowledge."

    tool_list_str = ", ".join([f"`{t.value}`" for t in allowed_tools])

    prompt_template = get_prompt("build_context_prompt")
    system_prompt = prompt_template.replace("{{TOOL_LIST}}", tool_list_str).replace(
        "{{RAG_RULE}}", rag_rule
    )
    return system_prompt


class PromptConfig:
    def __init__(
        self,
        epic_plan_system_prompt: str | None = None,
        epic_plan_review_prompt: str | None = None,
        planning_system_prompt: str | None = None,
        planning_review_prompt: str | None = None,
        implementation_investigate_prompt: str | None = None,
        implementation_draft_prompt: str | None = None,
        implementation_review_prompt: str | None = None,
        file_overview_prompt: str | None = None,
        merge_overview_prompt: str | None = None,
        summarization_system_prompt: str | None = None,
        index_search_prompt: str | None = None,
        build_context_prompt: str | None = None,
        ask_llm_system_prompt: str | None = None,
        research_system_prompt: str | None = None,
        browse_system_prompt: str | None = None,
        user_prefix: str = "[Coding Agent — user request]",
    ) -> None:
        self.epic_plan_system_prompt: str = epic_plan_system_prompt or get_prompt(
            "epic_plan_system_prompt"
        )
        self.epic_plan_review_prompt: str = epic_plan_review_prompt or get_prompt(
            "epic_plan_review_prompt"
        )
        self.planning_system_prompt: str = planning_system_prompt or get_prompt(
            "planning_system_prompt"
        )
        self.planning_review_prompt: str = planning_review_prompt or get_prompt(
            "planning_review_prompt"
        )
        self.implementation_investigate_prompt: str = (
            implementation_investigate_prompt
            or get_prompt("implementation_investigate_prompt")
        )
        self.implementation_draft_prompt: str = (
            implementation_draft_prompt or get_prompt("implementation_draft_prompt")
        )
        self.implementation_review_prompt: str = (
            implementation_review_prompt or get_prompt("implementation_review_prompt")
        )
        self.file_overview_prompt: str = file_overview_prompt or get_prompt(
            "file_overview_prompt"
        )
        self.merge_overview_prompt: str = merge_overview_prompt or get_prompt(
            "merge_overview_prompt"
        )
        self.summarization_system_prompt: str = (
            summarization_system_prompt or get_prompt("summarization_system_prompt")
        )
        self.index_search_prompt: str = index_search_prompt or get_prompt(
            "index_search_prompt"
        )
        self.build_context_prompt: str = (
            build_context_prompt or get_build_context_prompt()
        )
        self.ask_llm_system_prompt: str = ask_llm_system_prompt or get_prompt(
            "ask_llm_system_prompt"
        )
        self.research_system_prompt: str = research_system_prompt or get_prompt(
            "research_system_prompt"
        )
        self.browse_system_prompt: str = browse_system_prompt or get_prompt(
            "browse_system_prompt"
        )
        self.user_prefix: str = user_prefix

        self.build_context_tools = [
            ToolName.INVESTIGATE_FILE,
            ToolName.SEARCH_CODE,
            ToolName.WEB_SEARCH,
            ToolName.GET_SKILL_CONTENT,
            ToolName.INCLUDE_IN_CONTEXT,
            ToolName.EXCLUDE_FROM_CONTEXT,
        ]
        if settings.use_rag:
            self.build_context_tools.append(ToolName.SEARCH_LOCAL_DOCUMENTS)


default_prompt_config = PromptConfig()
