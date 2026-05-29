from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool

from core.container import AgentContainer, get_container, Llm
from core.exceptions import AgentInvocationError, MCPConnectionError, MCPToolError
from core.agent_tools import ToolName, build_tools
from core.schemas import PlanResponse
from lib.helpers import extract_text_response, extract_read_files
from lib.logger import get_logger

logger = get_logger(__name__)

TOTAL_ROUNDS = 3


def _render_clarifications(args: dict) -> str:
    questions = args.get("questions") or []
    options = args.get("options") or []
    answer_template = args.get("answer_template") or ""

    lines: list[str] = []
    for i, q in enumerate(questions, start=1):
        lines.append(f"**Q{i}: {q}**")
        opts = options[i - 1] if i - 1 < len(options) else []
        for opt in opts:
            lines.append(f"- {opt}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("Reply with your answers:")
    lines.append("")
    lines.append(
        answer_template.strip()
        or "\n".join(f"Q{i}: _" for i in range(1, len(questions) + 1))
    )

    return "\n".join(lines)


def _render_read_files(files: dict[str, str]) -> str:
    if not files:
        return ""
    parts = []
    for path, content in files.items():
        parts.append(f"# {path}\n\n{content}")
    return "\n\n".join(parts)


async def _run_tool_loop(
    llm: Llm,
    llm_with_tools: Llm,
    tools: list[BaseTool],
    initial_messages: list[BaseMessage],
) -> tuple[AIMessage, list[BaseMessage]]:
    tool_map = {t.name: t for t in tools}
    messages: list[BaseMessage] = list(initial_messages)

    for round_num in range(1, TOTAL_ROUNDS + 1):
        logger.info(f"planner.call_llm round={round_num} messages={len(messages)}")
        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)

        tool_calls = getattr(response, "tool_calls", []) or []
        if not tool_calls:
            return response, messages

        if any(call["name"] == ToolName.ASK_CLARIFICATION.value for call in tool_calls):
            return response, messages

        for call in tool_calls:
            tool_name = call["name"]
            tool_args = call["args"]
            try:
                logger.info(
                    f"planner.execute_tool tool={tool_name}",
                    extra={"tool_args": tool_args},
                )
                result = await tool_map[tool_name].ainvoke(tool_args)
                messages.append(
                    ToolMessage(content=str(result), tool_call_id=call["id"])
                )
            except Exception as exc:
                logger.exception(f"planner tool {tool_name} failed")
                messages.append(
                    ToolMessage(content=f"Error: {exc}", tool_call_id=call["id"])
                )

    logger.info("planner.tool_loop exhausted round budget; forcing final response")
    nudge = HumanMessage(
        content=(
            "Tool-call budget reached. Produce the final Plan now using the context gathered."
        )
    )
    final = await llm.ainvoke(messages + [nudge])
    messages.append(nudge)
    messages.append(final)
    return final, messages


async def main(prompt: str, container: AgentContainer | None = None) -> PlanResponse:
    resolved = container or get_container()

    tools = build_tools(
        resolved.mcp_client,
        resolved.web_search,
        allowed_tools=[ToolName.GET_FILE_TEXT, ToolName.ASK_CLARIFICATION],
    )
    llm_with_tools = resolved.llm_creative.bind_tools(tools)

    context_message = HumanMessage(
        content=f"{resolved.prompt_config.user_prefix}\n{prompt}\n"
    )
    initial_messages: list[BaseMessage] = [
        context_message,
        SystemMessage(content=resolved.prompt_config.planning_system_prompt),
    ]

    try:
        draft_response, history = await _run_tool_loop(
            resolved.llm_creative, llm_with_tools, tools, initial_messages
        )
    except (MCPConnectionError, MCPToolError):
        raise
    except Exception as exc:
        logger.exception("LLM invocation failed during planning")
        raise AgentInvocationError(f"LLM invocation failed: {exc}") from exc

    read_files = extract_read_files(history)
    loaded_files = list(read_files.keys())

    clarification_calls = [
        c
        for c in (getattr(draft_response, "tool_calls", []) or [])
        if c["name"] == ToolName.ASK_CLARIFICATION.value
    ]
    if clarification_calls:
        summary = _render_clarifications(clarification_calls[0]["args"])
        return PlanResponse(summary=summary, loaded_files=loaded_files)

    draft_plan = extract_text_response([draft_response])
    if not draft_plan:
        raise AgentInvocationError("LLM returned an empty response")

    read_files_block = _render_read_files(read_files)

    review_messages: list[BaseMessage] = [context_message]
    if read_files_block:
        review_messages.append(HumanMessage(content=read_files_block))
    review_messages.append(
        SystemMessage(content=resolved.prompt_config.planning_review_prompt)
    )
    review_messages.append(HumanMessage(content=f"### Draft Plan\n\n{draft_plan}"))

    try:
        final_response = await resolved.llm_balanced.ainvoke(review_messages)
    except Exception as exc:
        logger.exception("LLM invocation failed during plan review")
        raise AgentInvocationError(f"LLM invocation failed on step 2: {exc}") from exc

    content = extract_text_response([final_response])
    if not content:
        raise AgentInvocationError("LLM returned an empty response during plan review")

    return PlanResponse(summary=content.strip(), loaded_files=loaded_files)
