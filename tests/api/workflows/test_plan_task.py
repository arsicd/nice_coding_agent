import pytest
from langchain_core.messages import AIMessage

from core.schemas import PlanResponse
from core.workflows import plan_task as module
from tests.fakes.fake_container import FakeBoundLLM, FakeContainer


def make_container(responses_creative, responses_balanced):
    container = FakeContainer(
        overview_text="",
        llm_responses_creative=responses_creative,
        llm_responses_balanced=responses_balanced,
    )
    return container


@pytest.mark.asyncio
async def test_main_plan_mode_runs_review_and_returns_final_plan():
    prompt = "build a feature"
    container = make_container(
        [
            AIMessage(content="<plan>draft plan</plan>"),
        ],
        [
            AIMessage(content="<plan>final reviewed plan</plan>"),
        ],
    )

    result = await module.main(prompt, container=container)

    assert result == PlanResponse(
        summary="<plan>final reviewed plan</plan>", loaded_files=[]
    )
    assert len(container.llm_creative.bound_llm.invocations) == 1
    assert len(container.llm_balanced.bound_llm.invocations) == 1

    first_invocation = container.llm_creative.bound_llm.invocations[0]
    assert len(first_invocation) == 2
    assert first_invocation[0].content == f"[Coding Agent — user request]\n{prompt}\n"
    assert container.prompt_config.planning_system_prompt in first_invocation[1].content

    second_invocation = container.llm_balanced.bound_llm.invocations[0]
    assert len(second_invocation) == 3
    assert second_invocation[0].content == f"[Coding Agent — user request]\n{prompt}\n"
    assert (
        container.prompt_config.planning_review_prompt in second_invocation[1].content
    )
    assert second_invocation[2].content == "### Draft Plan\n\n<plan>draft plan</plan>"


@pytest.mark.asyncio
async def test_main_empty_review_response_raises_error():
    container = make_container(
        [
            AIMessage(content="<plan>draft plan</plan>"),
        ],
        [
            AIMessage(content=""),
        ],
    )

    with pytest.raises(
        module.AgentInvocationError, match="empty response during plan review"
    ):
        await module.main("build a feature", container=container)
