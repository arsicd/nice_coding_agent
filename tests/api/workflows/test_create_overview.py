from types import SimpleNamespace

import pytest

from core.workflows import create_overview
from core.workflows.create_file_index import OVERVIEW_FILE_NAME
from lib.helpers import context_size


class FakeMCPClient:
    def __init__(self) -> None:
        self.created_files: list[tuple[str, str]] = []

    async def list_directory_tree(self) -> str:
        return "project/\n  app.py"

    async def create_file(self, path: str, content: str) -> None:
        self.created_files.append((path, content))


class FakeLLM:
    def __init__(self, content: str) -> None:
        self.content = content
        self.messages = None

    async def ainvoke(self, messages):
        self.messages = messages
        return SimpleNamespace(content=self.content)


@pytest.mark.asyncio
async def test_main_returns_success_message_with_file_index_token_count(
    monkeypatch,
) -> None:
    file_index = "# File Index\n\n- app.py: main app entry"
    fake_llm = FakeLLM("merged overview")
    container = SimpleNamespace(
        mcp_client=FakeMCPClient(),
        llm_strict=fake_llm,
        prompt_config=SimpleNamespace(merge_overview_prompt="merge prompt"),
    )

    async def fake_main_create_file_index(_container) -> str:
        return file_index

    monkeypatch.setattr(
        create_overview, "main_create_file_index", fake_main_create_file_index
    )
    monkeypatch.setattr(
        create_overview,
        "parse_tree_to_nodes",
        lambda _tree, **_kwargs: [{"label": "project", "children": []}],
    )
    monkeypatch.setattr(
        create_overview, "format_tree_as_text", lambda _nodes: "project"
    )

    result = await create_overview.main(container)

    assert result == (f"Created overview. Index size: {context_size(file_index):,} tok")


@pytest.mark.asyncio
async def test_main_writes_overview_file_and_preserves_existing_side_effects(
    monkeypatch,
) -> None:
    fake_mcp = FakeMCPClient()
    fake_llm = FakeLLM("merged overview body")
    container = SimpleNamespace(
        mcp_client=fake_mcp,
        llm_strict=fake_llm,
        prompt_config=SimpleNamespace(merge_overview_prompt="merge prompt"),
    )

    async def fake_main_create_file_index(_container) -> str:
        return "index content"

    monkeypatch.setattr(
        create_overview, "main_create_file_index", fake_main_create_file_index
    )
    monkeypatch.setattr(
        create_overview,
        "parse_tree_to_nodes",
        lambda _tree, **_kwargs: [{"label": "project", "children": []}],
    )
    monkeypatch.setattr(
        create_overview, "format_tree_as_text", lambda _nodes: "project"
    )

    await create_overview.main(container)

    assert fake_mcp.created_files == [(OVERVIEW_FILE_NAME, "merged overview body")]
