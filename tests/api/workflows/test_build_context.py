import pytest
from dataclasses import dataclass
from langchain_core.messages import AIMessage

from core.schemas import ContentType
from core.workflows import build_context as module
from tests.fakes.fake_container import FakeTool, FakeContainer


@pytest.fixture
def fake_env(monkeypatch):
    overview_text = "fake overview text"
    file_index = "fake file index\n"
    skills = "Skill1\nSkill2"
    tools = {
        "include_in_context": FakeTool("include_in_context", "INCLUDE_REQUESTED"),
        "get_skill_content": FakeTool("get_skill_content", "fake skill content"),
        "web_search": FakeTool("web_search", "raw web search result"),
    }

    def fake_build_tools(mcp_client, web_search, allowed_tools):
        return [
            tools["include_in_context"],
            tools["get_skill_content"],
            tools["web_search"],
        ]

    async def fake_list_skills_tool():
        return skills

    # Mock indexing dependencies
    monkeypatch.setattr(module, "parse_tree_to_nodes", lambda tree, excluded=None: [])
    monkeypatch.setattr(module, "all_tree_files", lambda nodes: [])

    @dataclass
    class Stats:
        indexed: int = 0
        skipped: int = 0
        emptied: int = 0
        failed: int = 0
        orphans_deleted: int = 0

    monkeypatch.setattr(module, "index_files", lambda paths, root, force: Stats())

    class MockSettings:
        project_root = "/tmp/fake_project"

    monkeypatch.setattr(module, "settings", MockSettings())

    monkeypatch.setattr(module, "build_tools", fake_build_tools)
    monkeypatch.setattr(module, "list_skills_tool", fake_list_skills_tool)

    return {
        "overview_text": overview_text,
        "file_index": file_index,
        "skills": skills,
        "tools": tools,
    }


@pytest.mark.asyncio
async def test_main_happy_path_three_tool_rounds(fake_env):
    responses = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "1",
                    "name": "include_in_context",
                    "args": {"paths": ["src/app.py"]},
                }
            ],
        ),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "2",
                    "name": "get_skill_content",
                    "args": {"filename": "skill_a.md"},
                }
            ],
        ),
        AIMessage(
            content="",
            tool_calls=[
                {"id": "3", "name": "web_search", "args": {"query": "python testing"}}
            ],
        ),
        AIMessage(content="done"),
    ]
    container = FakeContainer(fake_env["overview_text"], llm_responses_strict=responses)
    container.mcp_client.tree_text = fake_env["file_index"]
    container.mcp_client.file_content_overrides["src/app.py"] = "fake file content"

    parts = await module.main("user instruction", container=container)

    assert len(parts) == 4
    assert parts[0].title == "Project Overview"
    assert parts[0].content == fake_env["overview_text"]
    assert parts[0].type == ContentType.project_overview

    assert parts[1].title == "src/app.py"
    assert parts[1].content == "fake file content"
    assert parts[1].type == ContentType.file

    assert parts[2].title == "skill_a.md"
    assert parts[2].content == "fake skill content"
    assert parts[2].type == ContentType.skill

    assert parts[3].title == "🔍 web_search: python testing"
    assert parts[3].content == "raw web search result"
    assert parts[3].type == ContentType.web_search

    assert len(container.llm_strict.bound_llm.invocations) == 4
    assert fake_env["tools"]["include_in_context"].calls == []
    assert fake_env["tools"]["get_skill_content"].calls == [{"filename": "skill_a.md"}]
    assert fake_env["tools"]["web_search"].calls == [{"query": "python testing"}]

    first_human = container.llm_strict.bound_llm.invocations[0][1].content
    assert "# File Tree" in first_human
    assert "fake file index" in first_human
    assert "# Available Skills" in first_human
    assert fake_env["skills"] in first_human
    assert "# User Instruction" in first_human
    assert "user instruction" in first_human


@pytest.mark.asyncio
async def test_main_no_tool_calls_returns_initial_overview_only(fake_env):
    responses = [AIMessage(content="done")]
    container = FakeContainer(fake_env["overview_text"], llm_responses_strict=responses)
    container.mcp_client.tree_text = fake_env["file_index"]

    parts = await module.main("user instruction", container=container)

    assert len(parts) == 1
    assert parts[0].title == "Project Overview"
    assert parts[0].content == fake_env["overview_text"]
    assert parts[0].type == ContentType.project_overview
    assert len(container.llm_strict.bound_llm.invocations) == 1
    assert fake_env["tools"]["include_in_context"].calls == []
    assert fake_env["tools"]["get_skill_content"].calls == []
    assert fake_env["tools"]["web_search"].calls == []
