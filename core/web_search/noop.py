from dataclasses import dataclass

from core.web_search.base import SearchManager
from lib.logger import get_logger

logger = get_logger(__name__)


@dataclass
class NoopSearch(SearchManager):

    async def web_search(
        self, query: str, num_results: int, max_characters: int
    ) -> list[str]:
        logger.warning("Configure web search to get better results")
        raise NotImplementedError("No web search configured")
