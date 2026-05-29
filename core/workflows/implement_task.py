from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool

from core.agent_tools import ToolName, build_tools
from core.container import AgentContainer, get_container, Llm
from core.exceptions import AgentInvocationError
from core.schemas import CodeChangeResponse
from lib.logger import get_logger

logger = get_logger(__name__)

TOTAL_ROUNDS = 6


def _extract_verification_notes(
    history: list[BaseMessage], max_output_chars: int = 800
) -> str:
    include_tools = {ToolName.RUN_SCRATCH_CODE.value}

    call_index: dict[str, tuple[str, dict]] = {}
    for msg in history:
        if isinstance(msg, AIMessage):
            for call in getattr(msg, "tool_calls", []) or []:
                call_index[call["id"]] = (call["name"], call.get("args") or {})

    notes: list[str] = []
    for msg in history:
        if not isinstance(msg, ToolMessage):
            continue
        call = call_index.get(msg.tool_call_id)
        if not call:
            continue
        tool_name, args = call
        if tool_name not in include_tools:
            continue

        code = (args.get("code") or "").strip()
        output = str(msg.content).strip()
        if len(output) > max_output_chars:
            output = output[:max_output_chars] + "\n... [truncated]"

        notes.append(f"Code executed:\n```\n{code}\n```\n\nResult:\n```\n{output}\n```")

    if not notes:
        return ""

    return "\n\n---\n\n".join(notes)


async def _run_tool_loop(
    llm_with_tools: Llm, tools: list[BaseTool], initial_messages: list[BaseMessage]
) -> list[BaseMessage]:
    tool_map = {t.name: t for t in tools}
    messages: list[BaseMessage] = list(initial_messages)

    for round_num in range(1, TOTAL_ROUNDS + 1):
        logger.info(f"implementer.call_llm round={round_num} messages={len(messages)}")
        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)

        tool_calls = getattr(response, "tool_calls", []) or []
        if not tool_calls:
            return messages

        for call in tool_calls:
            tool_name = call["name"]
            tool_args = call["args"]
            try:
                logger.info(
                    f"implementer.execute_tool tool={tool_name}",
                    extra={"tool_args": tool_args},
                )
                result = await tool_map[tool_name].ainvoke(tool_args)
                messages.append(
                    ToolMessage(content=str(result), tool_call_id=call["id"])
                )
            except Exception as exc:
                logger.exception(f"implementer tool {tool_name} failed")
                messages.append(
                    ToolMessage(content=f"Error: {exc}", tool_call_id=call["id"])
                )

    logger.info("implementer.tool_loop exhausted round budget")
    return messages


async def main(
    prompt: str, container: AgentContainer | None = None
) -> CodeChangeResponse:
    resolved = container or get_container()

    tools = build_tools(
        resolved.mcp_client,
        resolved.web_search,
        allowed_tools=[ToolName.RUN_SCRATCH_CODE],
    )
    llm_with_tools = resolved.llm_coding.bind_tools(tools)

    context_message = HumanMessage(
        content=f"{resolved.prompt_config.user_prefix}\n{prompt}\n"
    )
    initial_messages: list[BaseMessage] = [
        context_message,
        SystemMessage(content=resolved.prompt_config.implementation_investigate_prompt),
    ]

    history = await _run_tool_loop(llm_with_tools, tools, initial_messages)

    draft_messages: list[BaseMessage] = [
        context_message,
        SystemMessage(content=resolved.prompt_config.implementation_draft_prompt),
    ]
    draft_messages.extend(history[2:])

    try:
        draft_result = await resolved.llm_coding.ainvoke_structured(
            CodeChangeResponse, draft_messages
        )
    except Exception as exc:
        logger.exception("Draft implementation invocation failed")
        raise AgentInvocationError(
            f"Draft implementation invocation failed: {exc}"
        ) from exc

    verification_notes = _extract_verification_notes(history)
    review_messages = [
        context_message,
        SystemMessage(content=resolved.prompt_config.implementation_review_prompt),
    ]
    if verification_notes:
        review_messages.append(
            HumanMessage(
                content=(
                    "[Verification performed during draft]\n\n"
                    "Treat these results as established facts unless clearly wrong.\n\n"
                    f"{verification_notes}"
                )
            )
        )
    review_messages.append(
        HumanMessage(
            content=f"[Draft CodeChangeResponse]\n\n{draft_result.model_dump_json(indent=2)}"
        )
    )

    try:
        result = await resolved.llm_coding.ainvoke_structured(
            CodeChangeResponse, review_messages
        )
    except Exception as exc:
        logger.exception("Review implementation invocation failed")
        raise AgentInvocationError(
            f"Review implementation invocation failed: {exc}"
        ) from exc

    for change in result.changes:
        change.is_new_file = not bool(change.old_text.strip())
    return result
