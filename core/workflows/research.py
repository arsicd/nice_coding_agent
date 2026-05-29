import json
from typing import Annotated, TypedDict

from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
    ToolMessage,
)
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from core.config import settings
from core.container import AgentContainer, get_container
from core.exceptions import AgentInvocationError
from core.agent_tools import ToolName, build_tools, TOOL_ERROR_PREFIX
from core.workflows.summarize_item import main as summarize_item
from lib.logger import get_logger
from lib.helpers import extract_text_response
from core.workflows.create_file_index import OVERVIEW_FILE_NAME

logger = get_logger(__name__)

TOTAL_ROUNDS = 4

FINAL_ROUND_RESEARCH_PROMPT = (
    "You have finished gathering information. "
    "Now synthesize everything into a final, structured Markdown response. "
    "Do not request any more tools. "
    "Cite file paths or URLs inline where relevant."
)

_SKIPPED_TOOL_CALL_STUB = "(tool call skipped: research budget exhausted)"


class ResearchState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    question: str
    round_num: int


def build_graph(container: AgentContainer, num_rounds: int) -> StateGraph:
    allowed_tools = [
        ToolName.SEARCH_CODE,
        ToolName.GET_FILE_TEXT,
        ToolName.WEB_SEARCH,
    ]
    if settings.use_rag:
        allowed_tools.append(ToolName.SEARCH_LOCAL_DOCUMENTS)
    tools = build_tools(
        container.mcp_client, container.web_search, allowed_tools=allowed_tools
    )
    llm_with_tools = container.llm_balanced.bind_tools(tools)

    async def init_prompt(state: ResearchState) -> dict:
        try:
            overview = await container.mcp_client.get_file_text(OVERVIEW_FILE_NAME)
        except FileNotFoundError:
            overview = ""
        file_tree = await container.mcp_client.list_directory_tree()
        prompt = (
            f"{overview}\n\n"
            f"# File Tree\n{json.loads(file_tree)["tree"]}\n\n"
            f"# User Instruction\n{state['question']}\n"
        )
        return {
            "messages": [
                SystemMessage(content=container.prompt_config.research_system_prompt),
                HumanMessage(content=prompt),
            ]
        }

    async def call_llm(state: ResearchState) -> dict:
        logger.info(
            f"call_llm round={state['round_num']} messages={len(state['messages'])}"
        )

        if state["round_num"] >= num_rounds:
            messages = list(state["messages"]) + [
                SystemMessage(content=FINAL_ROUND_RESEARCH_PROMPT)
            ]
            model = container.llm_balanced
        else:
            messages = state["messages"]
            model = llm_with_tools
        response = await model.ainvoke(messages)
        return {"messages": [response]}

    async def force_final_synthesis(state: ResearchState) -> dict:
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
            + [SystemMessage(content=FINAL_ROUND_RESEARCH_PROMPT)]
        )
        response = await container.llm_balanced.ainvoke(messages)
        return {"messages": stubs + [response]}

    async def execute_tools(state: ResearchState) -> dict:
        last_msg = state["messages"][-1]
        tool_calls = getattr(last_msg, "tool_calls", [])
        tool_map = {t.name: t for t in tools}
        tool_messages = []
        for call in tool_calls:
            tool_name = call["name"]
            tool_args = call["args"]
            logger.info(f"Executing tool: {tool_name}", extra={"tool_args": tool_args})
            result = await tool_map[tool_name].ainvoke(tool_args)
            result_str = str(result)
            if tool_name == ToolName.WEB_SEARCH.value and not result_str.startswith(
                TOOL_ERROR_PREFIX
            ):
                result_str = await summarize_item(
                    result_str, state["question"], container
                )
            tool_messages.append(
                ToolMessage(content=result_str, tool_call_id=call["id"])
            )
        return {"messages": tool_messages, "round_num": state["round_num"] + 1}

    def route_after_llm(state: ResearchState):
        has_tool_calls = bool(getattr(state["messages"][-1], "tool_calls", []))
        if not has_tool_calls:
            return END
        if state["round_num"] < num_rounds:
            return "execute_tools"
        return "force_final_synthesis"

    b = StateGraph(ResearchState)
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
    question: str,
    container: AgentContainer | None = None,
) -> str:
    resolved = container or get_container()
    graph = build_graph(resolved, TOTAL_ROUNDS)
    state = await graph.ainvoke({"messages": [], "question": question, "round_num": 0})
    answer = extract_text_response([state["messages"][-1]])
    if not answer:
        raise AgentInvocationError("LLM returned an empty response")
    logger.info(
        f"Done in {state['round_num']} rounds, {len(state['messages'])} messages"
    )
    return answer
