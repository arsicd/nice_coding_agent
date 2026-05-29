from langchain_core.messages import HumanMessage, SystemMessage

from core.container import AgentContainer, get_container
from core.exceptions import AgentInvocationError
from lib.logger import get_logger
from lib.helpers import extract_text_response

EPIC_PLAN_FILE_NAME = ".nice/epic_plan.md"

logger = get_logger(__name__)


async def main(instructions: str, container: AgentContainer | None = None) -> str:
    resolved = container or get_container()

    context_message = HumanMessage(
        content=f"{resolved.prompt_config.user_prefix}\n{instructions}\n"
    )
    messages = [
        context_message,
        SystemMessage(content=resolved.prompt_config.epic_plan_system_prompt),
    ]

    try:
        response = await resolved.llm_creative.ainvoke(messages)
    except Exception as exc:
        logger.exception("LLM invocation failed")
        raise AgentInvocationError(f"LLM invocation failed: {exc}") from exc

    draft_plan = extract_text_response([response])

    review_messages = [
        context_message,
        SystemMessage(content=resolved.prompt_config.epic_plan_review_prompt),
        HumanMessage(content=f"[Draft Plan]\n\n{draft_plan}"),
    ]

    try:
        final_response = await resolved.llm_balanced.ainvoke(review_messages)
    except Exception as exc:
        logger.exception("LLM invocation failed during plan review")
        raise AgentInvocationError(f"LLM invocation failed on step 2: {exc}") from exc

    final_plan = extract_text_response([final_response])

    await resolved.mcp_client.create_file(EPIC_PLAN_FILE_NAME, final_plan)

    return final_plan
