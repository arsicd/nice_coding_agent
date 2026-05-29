from langchain_core.messages import HumanMessage, SystemMessage
from core.container import AgentContainer, get_container
from core.exceptions import AgentInvocationError
from lib.logger import get_logger
from lib.helpers import extract_text_response

logger = get_logger(__name__)


async def main(question: str, container: AgentContainer | None = None) -> str:
    resolved = container or get_container()
    system_prompt = resolved.prompt_config.ask_llm_system_prompt
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=question),
    ]
    try:
        response = await resolved.llm_balanced.ainvoke(messages)
    except Exception as exc:
        logger.exception("LLM standalone question failed")
        raise AgentInvocationError(f"LLM call failed: {exc}") from exc
    answer = extract_text_response([response])
    if not answer:
        raise AgentInvocationError("LLM returned an empty response")
    return answer
