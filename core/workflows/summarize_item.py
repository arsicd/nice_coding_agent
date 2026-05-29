from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

from core.container import AgentContainer, get_container
from core.exceptions import AgentInvocationError
from lib.logger import get_logger
from lib.helpers import extract_text_response

logger = get_logger(__name__)


async def main(
    content: str, instructions: str, container: AgentContainer | None = None
) -> str:
    resolved = container or get_container()

    system_prompt = resolved.prompt_config.summarization_system_prompt
    enriched = f"{system_prompt}\n\n### Context to Summarize\n{content}\n\n### Current Instructions\n{instructions}"
    messages = [
        SystemMessage(content=enriched),
        HumanMessage(
            content="Summarize the context above for the current instructions."
        ),
    ]

    try:
        response = await resolved.llm_strict.ainvoke(messages)
    except Exception as exc:
        logger.exception("LLM summarization failed")
        raise AgentInvocationError(f"LLM summarization failed: {exc}") from exc

    summary = extract_text_response([response])
    if not summary:
        raise AgentInvocationError("LLM returned an empty summary")

    return summary
