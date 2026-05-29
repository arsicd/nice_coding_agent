from typing import Annotated, TypedDict

from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from core.container import AgentContainer, get_container
from core.exceptions import AgentInvocationError
from lib.logger import get_logger
from lib.helpers import extract_text_response

logger = get_logger(__name__)

TOTAL_ROUNDS = 16

FINAL_ROUND_BROWSE_PROMPT = (
    "You have used your full browsing budget. "
    "Stop calling tools and write your final answer now as structured Markdown. "
    "Include exact values, URLs, and any element refs that mattered. "
    "If you could not complete the task, say so explicitly and explain what "
    "you saw and what blocked you."
)

_SKIPPED_TOOL_CALL_STUB = "(tool call skipped: browse budget exhausted)"


class BrowseState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    instruction: str
    round_num: int


def build_graph(
    container: AgentContainer,
    playwright_tools: list[BaseTool],
    num_rounds: int,
) -> StateGraph:
    llm_with_tools = container.llm_balanced.bind_tools(playwright_tools)
    tool_map = {t.name: t for t in playwright_tools}

    async def init_prompt(state: BrowseState) -> dict:
        return {
            "messages": [
                SystemMessage(content=container.prompt_config.browse_system_prompt),
                HumanMessage(content=state["instruction"]),
            ]
        }

    async def call_llm(state: BrowseState) -> dict:
        logger.info(
            f"call_llm round={state['round_num']} messages={len(state['messages'])}"
        )

        if state["round_num"] >= num_rounds:
            messages = list(state["messages"]) + [
                SystemMessage(content=FINAL_ROUND_BROWSE_PROMPT)
            ]
            model = container.llm_balanced
        else:
            messages = state["messages"]
            model = llm_with_tools
        response = await model.ainvoke(messages)
        return {"messages": [response]}

    async def force_final_synthesis(state: BrowseState) -> dict:
        logger.info(
            "force_final_synthesis: model emitted tool calls on final round; "
            "forcing synthesis"
        )
        last_msg = state["messages"][-1]
        tool_calls = getattr(last_msg, "tool_calls", [])
        stubs = [
            ToolMessage(
                content=_SKIPPED_TOOL_CALL_STUB,
                tool_call_id=call["id"],
            )
            for call in tool_calls
        ]
        messages = (
            list(state["messages"])
            + stubs
            + [SystemMessage(content=FINAL_ROUND_BROWSE_PROMPT)]
        )
        response = await container.llm_balanced.ainvoke(messages)
        return {"messages": stubs + [response]}

    async def execute_tools(state: BrowseState) -> dict:
        last_msg = state["messages"][-1]
        tool_calls = getattr(last_msg, "tool_calls", [])
        tool_messages = []
        for call in tool_calls:
            tool_name = call["name"]
            tool_args = call["args"]
            logger.info(f"Executing tool: {tool_name}", extra={"tool_args": tool_args})
            try:
                result = await tool_map[tool_name].ainvoke(tool_args)
                result_str = str(result)
            except KeyError:
                result_str = f"[Tool error] unknown tool '{tool_name}'"
            except Exception as exc:
                logger.warning("%s failed: %s", tool_name, exc)
                result_str = f"[Tool error] '{tool_name}' failed: {exc}"
            tool_messages.append(
                ToolMessage(content=result_str, tool_call_id=call["id"], name=tool_name)
            )
        return {"messages": tool_messages, "round_num": state["round_num"] + 1}

    def route_after_llm(state: BrowseState):
        has_tool_calls = bool(getattr(state["messages"][-1], "tool_calls", []))
        if not has_tool_calls:
            return END
        if state["round_num"] < num_rounds:
            return "execute_tools"
        return "force_final_synthesis"

    b = StateGraph(BrowseState)
    b.add_node("init_prompt", init_prompt)
    b.add_node("call_llm", call_llm)
    b.add_node("execute_tools", execute_tools)
    b.add_node("force_final_synthesis", force_final_synthesis)
    b.add_edge(START, "init_prompt")
    b.add_edge("init_prompt", "call_llm")
    b.add_conditional_edges(
        "call_llm",
        route_after_llm,
        {
            "execute_tools": "execute_tools",
            "force_final_synthesis": "force_final_synthesis",
            END: END,
        },
    )
    b.add_edge("execute_tools", "call_llm")
    b.add_edge("force_final_synthesis", END)
    return b.compile()


async def main(
    instruction: str,
    headless: bool = False,
    container: AgentContainer | None = None,
) -> str:
    resolved = container or get_container()

    mcp_client = MultiServerMCPClient(
        {
            "playwright": {
                "command": "npx",
                "args": [
                    "@playwright/mcp@latest",
                    "--browser=chrome",
                    "--no-sandbox",
                    *(["--headless"] if headless else []),
                ],
                "transport": "stdio",
            }
        }
    )

    async with mcp_client.session("playwright") as session:
        playwright_tools = await load_mcp_tools(session)
        logger.info("Loaded %d Playwright MCP tools", len(playwright_tools))

        graph = build_graph(resolved, playwright_tools, TOTAL_ROUNDS)
        state = await graph.ainvoke(
            {
                "messages": [],
                "instruction": instruction,
                "round_num": 0,
            }
        )

    answer = extract_text_response([state["messages"][-1]])
    if not answer:
        raise AgentInvocationError("LLM returned an empty response")
    logger.info(
        f"Done in {state['round_num']} rounds, {len(state['messages'])} messages"
    )
    return answer
