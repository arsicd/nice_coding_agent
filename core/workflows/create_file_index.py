import asyncio
import hashlib

from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from core.container import AgentContainer, get_container
from core.config import settings
from lib.helpers import extract_text_response
from lib.logger import get_logger
from lib.tree_parser import parse_tree_to_nodes, all_tree_files
from lib.treesitter_extractor import extract_signatures_from_content

logger = get_logger(__name__)

OVERVIEW_FILE_NAME = ".nice/project_overview.md"
FILE_INDEX_FILE_NAME = ".nice/file_index.md"
EXCLUDED_DIRS = ["tests"]

create_index_lock = asyncio.Lock()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    reraise=True,
)
async def _invoke_llm(llm, messages):
    return await llm.ainvoke(messages, timeout=30)


async def process_file(
    file_path: str, container: AgentContainer, semaphore: asyncio.Semaphore
) -> str | None:
    content = await container.mcp_client.get_file_text(file_path)
    if not content:
        return None

    content_hash = hashlib.sha256(content.encode()).hexdigest()
    cached = await container.overview_cache.get_cached_overview(file_path, content_hash)
    if cached:
        return cached

    async with semaphore:
        logger.info(f"Creating summary for {file_path}")
        signatures = extract_signatures_from_content(file_path, content)
        messages = [
            SystemMessage(content=container.prompt_config.file_overview_prompt),
            HumanMessage(
                content=f"FILE: {file_path}\n\n<structure>\n{signatures}\n</structure>\n\n{content}"
            ),
        ]

        try:
            response = await _invoke_llm(container.llm_summarization, messages)
        except Exception as exc:
            logger.error(f"LLM failed for {file_path}: {exc}")
            return None

        summary = extract_text_response([response])
        if signatures:
            summary += "\n- **Structure**:\n"
            summary += signatures
        await container.overview_cache.set_cached_overview(
            file_path, content_hash, summary
        )
        return summary


async def main(container: AgentContainer | None = None) -> str:
    async with create_index_lock:
        resolved = container or get_container()

        file_tree = await resolved.mcp_client.list_directory_tree()
        tree_nodes = parse_tree_to_nodes(file_tree, excluded=EXCLUDED_DIRS)
        files = all_tree_files(tree_nodes)

        semaphore = asyncio.Semaphore(settings.summarization_concurrency)

        file_summaries = await asyncio.gather(
            *(process_file(f, resolved, semaphore) for f in files),
            return_exceptions=True,
        )

        result = "\n\n".join(s for s in file_summaries if isinstance(s, str) and s)
        await resolved.mcp_client.create_file(FILE_INDEX_FILE_NAME, result)

        return result
