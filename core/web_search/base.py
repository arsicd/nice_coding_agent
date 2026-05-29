from abc import ABC, abstractmethod


class SearchManager(ABC):
    @abstractmethod
    async def web_search(
        self, query: str, num_results: int, max_characters: int
    ) -> list[str]:
        raise NotImplementedError
