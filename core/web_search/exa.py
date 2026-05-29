from dataclasses import dataclass

from exa_py import Exa

from core.web_search.base import SearchManager


@dataclass
class ExaSearch(SearchManager):
    api_key: str

    def __post_init__(self):
        self.exa = Exa(self.api_key)

    async def web_search(
        self, query: str, num_results: int, max_characters: int
    ) -> list[str]:
        results = []
        pages = self.exa.search_and_contents(
            query, type="auto", num_results=10, highlights={"max_characters": 1000}
        )

        for page in pages.results:
            results.append(page.text)

        return results
