import asyncio
from pathlib import Path


from core.container import AgentContainer, get_container
from core.config import settings
from search.indexer import index_files
from lib.tree_parser import parse_tree_to_nodes, all_tree_files
from lib.treesitter_extractor import LANGUAGES
from lib.logger import get_logger

logger = get_logger(__name__)


async def index_project(container: AgentContainer | None = None) -> dict:
    container = container or get_container()
    project_root = str(Path(str(settings.project_root)).resolve())
    file_tree = await container.mcp_client.list_directory_tree()
    tree_nodes = parse_tree_to_nodes(file_tree, excluded=["tests"])
    relative_files = all_tree_files(tree_nodes)

    paths = [rel for rel in relative_files if Path(rel).suffix in LANGUAGES]

    logger.info(f"Indexing {len(paths)} project files")
    stats = await asyncio.to_thread(index_files, paths, project_root, True)
    logger.info(
        f"Index ready: indexed={stats.indexed} skipped={stats.skipped} "
        f"emptied={stats.emptied} failed={stats.failed} "
        f"orphans_deleted={stats.orphans_deleted}"
    )
    return {}
