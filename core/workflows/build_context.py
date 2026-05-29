import json
import operator
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
    ToolMessage,
)
from langgraph.graph import StateGraph, START, END

from core.container import AgentContainer, get_container
from core.exceptions import AgentInvocationError, MCPConnectionError, MCPToolError
from core.agent_tools import ToolName, build_tools, list_skills_tool
from core.config import settings
from core.schemas import ContextItem, ContentType
from core.workflows.create_file_index import OVERVIEW_FILE_NAME
from core.workflows.shared import index_project
from lib.logger import get_logger

logger = get_logger(__name__)

TOTAL_ROUNDS = 4


def _handle_included_files(current: set[str], delta: dict[str, bool]) -> set[str]:
    result = set(current)
    if not delta:
        return result
    for path, include in delta.items():
        if include:
            result.add(path)
        else:
            result.discard(path)
    return result


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    raw_prompt: str
    round_num: int
    context_parts: Annotated[list[ContextItem], operator.add]
    fetched_files: Annotated[set[str], operator.or_]
    included_files: Annotated[set[str], _handle_included_files]
    context_parts_final: list[ContextItem]


def build_graph(container) -> StateGraph:
    tools = build_tools(
        container.mcp_client,
        container.web_search,
        allowed_tools=container.prompt_config.build_context_tools,
    )

    llm_with_tools = container.llm_strict.bind_tools(tools)

    async def enrich_prompt(state: AgentState) -> dict:
        await index_project()
        skills = await list_skills_tool()
        context_parts = []
        try:
            overview = await container.mcp_client.get_file_text(OVERVIEW_FILE_NAME)
            context_parts.append(
                ContextItem(
                    title="Project Overview",
                    content=overview,
                    type=ContentType.project_overview,
                )
            )
        except FileNotFoundError:
            overview = ""
            logger.warning("Project Overview not found")
        file_tree = await container.mcp_client.list_directory_tree()
        prompt = (
            f"{overview}\n\n"
            f"# File Tree\n{json.loads(file_tree)["tree"]}\n\n"
            f"# Available Skills\n\n{skills}\n\n"
            f"# User Instruction\n{state['raw_prompt']}\n"
        )

        return {
            "messages": [
                SystemMessage(content=container.prompt_config.build_context_prompt),
                HumanMessage(content=prompt),
            ],
            "context_parts": context_parts,
        }

    async def call_llm(state: AgentState) -> dict:
        messages = list(state["messages"])
        if state["round_num"] == TOTAL_ROUNDS:
            messages.append(
                SystemMessage(
                    content=(
                        "This is your FINAL round. After this response, no further tool "
                        "rounds will execute. If you have identified files the planner "
                        "will need, call `include_in_context` now. Do NOT start new "
                        "`search_code` or `investigate_file` investigations — their results "
                        "will not reach you. If you are confident enough from earlier "
                        "investigation to include files, do so. Otherwise, finalize."
                    )
                )
            )
            logger.info("Last build context round reached")
        logger.info(f"call_llm {len(messages)} messages")
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    async def execute_tools(state: AgentState) -> dict:
        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", [])
        tool_map = {t.name: t for t in tools}

        tool_messages = []
        new_parts: list[ContextItem] = []
        newly_fetched: set[str] = set()
        inclusion_delta: dict[str, bool] = {}

        def _effectively_included(path_: str) -> bool:
            if path_ in inclusion_delta:
                return inclusion_delta[path_]
            return path_ in state["included_files"]

        def _already_emitted(path_: str) -> bool:
            if any(
                p.type == ContentType.file and p.title == path_
                for p in state["context_parts"]
            ):
                return True
            if any(p.type == ContentType.file and p.title == path_ for p in new_parts):
                return True
            return False

        for call in tool_calls:
            tool_name = call["name"]
            tool_args = call["args"]
            try:
                logger.info(
                    f"Executing tool: {tool_name}", extra={"tool_args": tool_args}
                )

                if tool_name == ToolName.INCLUDE_IN_CONTEXT.value:
                    paths = tool_args.get("paths", []) or []
                    included_now: list[str] = []
                    skipped_already: list[str] = []
                    errors: list[str] = []

                    for path in paths:
                        if _effectively_included(path):
                            skipped_already.append(path)
                            continue
                        try:
                            content = await container.mcp_client.get_file_text(path)
                        except Exception as fetch_exc:
                            logger.warning(
                                "include_in_context: failed to fetch '%s': %s",
                                path,
                                fetch_exc,
                            )
                            errors.append(f"{path} ({fetch_exc})")
                            continue
                        inclusion_delta[path] = True

                        if not _already_emitted(path):
                            new_parts.append(
                                ContextItem(
                                    title=path,
                                    content=content,
                                    type=ContentType.file,
                                )
                            )
                        included_now.append(path)

                    summary_parts = []
                    if included_now:
                        summary_parts.append(f"Included: {', '.join(included_now)}.")
                    if skipped_already:
                        summary_parts.append(
                            f"Already included: {', '.join(skipped_already)}."
                        )
                    if errors:
                        summary_parts.append(f"Errors: {'; '.join(errors)}.")
                    if not summary_parts:
                        summary_parts.append("No paths provided.")

                    tool_messages.append(
                        ToolMessage(
                            content=" ".join(summary_parts), tool_call_id=call["id"]
                        )
                    )
                    continue

                if tool_name == ToolName.EXCLUDE_FROM_CONTEXT.value:
                    paths = tool_args.get("paths", []) or []
                    excluded_now: list[str] = []
                    not_present: list[str] = []

                    for path in paths:
                        if _effectively_included(path):
                            inclusion_delta[path] = False
                            excluded_now.append(path)
                        else:
                            not_present.append(path)

                    summary_parts = []
                    if excluded_now:
                        summary_parts.append(f"Excluded: {', '.join(excluded_now)}.")
                    if not_present:
                        summary_parts.append(
                            f"Not currently included (no-op): {', '.join(not_present)}."
                        )
                    if not summary_parts:
                        summary_parts.append("No paths provided.")

                    tool_messages.append(
                        ToolMessage(
                            content=" ".join(summary_parts), tool_call_id=call["id"]
                        )
                    )
                    continue

                # All other tools: invoke and route their output as before.
                result = await tool_map[tool_name].ainvoke(tool_args)
                title = f"🛠️ {tool_name}"
                content_type = ContentType.general
                include_in_result = True

                if tool_name == ToolName.INVESTIGATE_FILE.value:
                    path = tool_args["path"]
                    if path in state["fetched_files"] or path in newly_fetched:
                        tool_messages.append(
                            ToolMessage(
                                content=f"(already investigated {path} earlier this run)",
                                tool_call_id=call["id"],
                            )
                        )
                        continue
                    newly_fetched.add(path)
                    result_str = str(result)
                    tool_messages.append(
                        ToolMessage(content=result_str, tool_call_id=call["id"])
                    )
                    continue
                elif tool_name == ToolName.GET_SKILL_CONTENT.value:
                    content_type = ContentType.skill
                    title = tool_args["filename"]
                elif tool_name == ToolName.WEB_SEARCH.value:
                    content_type = ContentType.web_search
                    title = f"🔍 {tool_name}: {tool_args['query']}"
                elif tool_name == ToolName.SEARCH_CODE.value:
                    title = f"🔎 search_code: {tool_args['query']}"
                    include_in_result = False

                tool_messages.append(
                    ToolMessage(content=str(result), tool_call_id=call["id"])
                )
                if include_in_result:
                    new_parts.append(
                        ContextItem(title=title, content=str(result), type=content_type)
                    )
            except Exception as e:
                logger.exception(f"Tool {tool_name} failed")
                new_parts.append(
                    ContextItem(title=f"⚠️ {tool_name} Error", content=f"Error: {e}")
                )
                tool_messages.append(
                    ToolMessage(content=f"Error: {e}", tool_call_id=call["id"])
                )

        return {
            "messages": tool_messages,
            "context_parts": new_parts,
            "round_num": state["round_num"] + 1,
            "fetched_files": newly_fetched,
            "included_files": inclusion_delta,
        }

    def route_after_llm(state: AgentState):
        has_tool_calls = bool(getattr(state["messages"][-1], "tool_calls", []))
        if has_tool_calls and state["round_num"] <= TOTAL_ROUNDS:
            return "execute_tools"
        return "build_final_context"

    def route_after_tools(state: AgentState):
        if state["round_num"] <= TOTAL_ROUNDS:
            return "call_llm"
        return "build_final_context"

    async def build_final_context(state: AgentState) -> dict:
        included = state["included_files"]
        filtered = [
            p
            for p in state["context_parts"]
            if p.type != ContentType.file or p.title in included
        ]
        logger.info(
            "build_final_context: applied final inclusion filter",
            extra={
                "included_count": len(included),
                "before": len(state["context_parts"]),
                "after": len(filtered),
            },
        )
        return {"context_parts_final": filtered}

    b = StateGraph(AgentState)
    b.add_node("enrich_prompt", enrich_prompt)
    b.add_node("call_llm", call_llm)
    b.add_node("execute_tools", execute_tools)
    b.add_node("build_final_context", build_final_context)

    b.add_edge(START, "enrich_prompt")
    b.add_edge("enrich_prompt", "call_llm")
    b.add_conditional_edges("call_llm", route_after_llm)
    b.add_conditional_edges("execute_tools", route_after_tools)
    b.add_edge("build_final_context", END)

    return b.compile()


async def main(
    instructions: str, container: AgentContainer | None = None
) -> list[ContextItem]:
    resolved = container or get_container()
    graph = build_graph(resolved)

    try:
        state = await graph.ainvoke(
            {
                "messages": [],
                "raw_prompt": instructions,
                "round_num": 1,
                "context_parts": [],
                "fetched_files": set(),
                "included_files": set(),
                "context_parts_final": [],
            },
            {"recursion_limit": settings.agent_max_steps},
        )
    except (MCPConnectionError, MCPToolError):
        raise
    except Exception as exc:
        cause = exc.__cause__ or exc
        if isinstance(cause, (MCPConnectionError, MCPToolError)):
            raise cause
        logger.exception("Unexpected error during context agent invocation")
        raise AgentInvocationError(f"Context Agent invocation failed: {exc}") from exc

    parts = state.get("context_parts_final") or []
    if not parts:
        raise AgentInvocationError("Agent completed but final context is empty.")

    logger.info(
        "run_agent completed (Context created locally)",
        extra={"parts_count": len(parts)},
    )
    return parts
