import pytest
from langchain_core.messages import AIMessage

from core.schemas import CodeChange, CodeChangeResponse
from core.workflows import implement_task as module
from tests.fakes.fake_container import FakeBoundLLM, FakeContainer


def make_container(responses):
    container = FakeContainer(overview_text="")
    container.llm_coding = type(container.llm_coding)(responses)
    container.prompt_config.implementation_investigate_prompt = (
        "implementation investigate prompt"
    )
    container.prompt_config.implementation_draft_prompt = "implementation draft prompt"
    container.prompt_config.implementation_review_prompt = (
        "implementation review prompt"
    )
    return container


@pytest.mark.asyncio
async def test_main_runs_review_and_returns_final_changes():
    prompt = "build a feature"
    container = make_container(
        [
            AIMessage(content="investigation complete"),
            AIMessage(
                content=(
                    '{"summary": "draft summary", "changes": ['
                    '{"file_path": "src/app.py", "description": "update app", '
                    '"old_text": "print(1)", "new_text": "print(2)"}]} '
                )
            ),
            AIMessage(
                content=(
                    '{"summary": "final summary", "changes": ['
                    '{"file_path": "src/new.py", "description": "add file", '
                    '"old_text": "", "new_text": "print(3)"}]} '
                )
            ),
        ]
    )
    container.llm_coding.bound_llm = FakeBoundLLM(
        container.llm_coding.bound_llm.responses
    )

    result = await module.main(prompt, container=container)

    assert result.summary == "final summary"
    assert len(result.changes) == 1
    change = result.changes[0]
    assert change.file_path == "src/new.py"
    assert change.description == "add file"
    assert change.old_text == ""
    assert change.new_text == "print(3)"
    assert change.is_new_file is True
    assert len(container.llm_coding.bound_llm.invocations) == 3

    tool_invocation = container.llm_coding.bound_llm.invocations[0]
    assert len(tool_invocation) == 2
    assert tool_invocation[0].content == f"[Coding Agent — user request]\n{prompt}\n"
    assert (
        container.prompt_config.implementation_investigate_prompt
        in tool_invocation[1].content
    )

    draft_invocation = container.llm_coding.bound_llm.invocations[1]
    assert len(draft_invocation) == 3
    assert draft_invocation[0].content == f"[Coding Agent — user request]\n{prompt}\n"
    assert (
        container.prompt_config.implementation_draft_prompt
        in draft_invocation[1].content
    )

    review_invocation = container.llm_coding.bound_llm.invocations[2]
    assert len(review_invocation) == 3
    assert review_invocation[0].content == f"[Coding Agent — user request]\n{prompt}\n"
    assert (
        container.prompt_config.implementation_review_prompt
        in review_invocation[1].content
    )
    assert review_invocation[2].content.startswith("[Draft CodeChangeResponse]\n\n")


@pytest.mark.asyncio
async def test_main_marks_existing_files_as_not_new():
    container = make_container(
        [
            AIMessage(content="investigation complete"),
            AIMessage(
                content=(
                    '{"summary": "final summary", "changes": ['
                    '{"file_path": "src/app.py", "description": "update app", '
                    '"old_text": "print(1)", "new_text": "print(2)"}]} '
                )
            ),
            AIMessage(
                content=(
                    '{"summary": "final summary", "changes": ['
                    '{"file_path": "src/app.py", "description": "update app", '
                    '"old_text": "print(1)", "new_text": "print(2)"}]} '
                )
            ),
        ]
    )
    container.llm_coding.bound_llm = FakeBoundLLM(
        container.llm_coding.bound_llm.responses
    )

    result = await module.main("build a feature", container=container)

    assert result.changes[0].is_new_file is False
    assert len(container.llm_coding.bound_llm.invocations) == 3
