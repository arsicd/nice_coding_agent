from langchain_core.messages import HumanMessage, SystemMessage

from core.container import AgentContainer, get_container
from core.exceptions import AgentInvocationError
from lib.helpers import extract_text_response
from lib.logger import get_logger
from lib.tree_parser import parse_tree_to_nodes, format_tree_as_text
from core.workflows.create_file_index import (
    main as main_create_file_index,
    OVERVIEW_FILE_NAME,
    EXCLUDED_DIRS,
)
from lib.helpers import context_size

logger = get_logger(__name__)


async def main(container: AgentContainer | None = None) -> str:
    resolved = container or get_container()

    file_tree = await resolved.mcp_client.list_directory_tree()
    tree_nodes = parse_tree_to_nodes(file_tree, excluded=EXCLUDED_DIRS)

    file_index = await main_create_file_index(resolved)

    merge_prompt = (
        f"<file_tree>\n{format_tree_as_text(tree_nodes)}\n</file_tree>\n\n"
        f"<file_summaries>\n{file_index}\n</file_summaries>"
    )

    messages = [
        SystemMessage(content=resolved.prompt_config.merge_overview_prompt),
        HumanMessage(content=merge_prompt),
    ]

    try:
        logger.info("Start merge summary")
        response = await resolved.llm_strict.ainvoke(messages)
        logger.info("End merge summary")
        result = extract_text_response([response])
        await resolved.mcp_client.create_file(OVERVIEW_FILE_NAME, result)
        token_count = context_size(file_index)
    except Exception as exc:
        logger.exception("LLM invocation failed")
        raise AgentInvocationError(f"LLM invocation failed: {exc}") from exc
    return f"Created overview. Index size: {token_count:,} tok"
