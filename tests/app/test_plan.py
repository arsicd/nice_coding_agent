from typing import Any

from core.schemas import PlanResponse
from app.events import Events
from app.presenter import AppPresenter
from app.state import AppState
from tests.fakes.fake_router import FakeRouter


async def test_plan_populates_state_with_result(
    app_presenter: AppPresenter,
    app_state: AppState,
    fake_router: FakeRouter,
    captured_events: list[tuple[str, Any]],
) -> None:
    fake_router.plan_task_result = PlanResponse(
        summary=(
            "Step 1: do the thing.\n\n"
            '<affected_files>{"files":[{"path":"app/main.py","action":"MODIFY","symbols":["main"]}]}</affected_files>\n\n'
            "Step 2: profit."
        )
    )
    app_state.add_context_entry(
        entry_id="ctx_seed",
        label="Seed",
        content="some context",
        raw_content="some context",
    )

    expected_prompt = app_state.build_llm_prompt()

    app_state.bus.on(
        Events.CONTEXT_CHANGED, lambda _p: captured_events.append((Events.CONTEXT_CHANGED, _p))
    )

    await app_presenter.on_plan()

    assert fake_router.calls == [("plan_task", (expected_prompt,), {})]

    plan_entries = [e for e in app_state.context_entries if e.label == "📋 Plan"]
    assert len(plan_entries) == 1
    plan = plan_entries[0]
    assert "<affected_files>" in plan.content
    assert "app/main.py" in plan.content
    assert plan.raw_content == plan.content.removeprefix("**Plan:**\n\n")
    assert plan.is_loading is False
    assert len(captured_events) >= 2


async def test_plan_preserves_original_summary_when_no_affected_files_block(
    app_presenter: AppPresenter,
    app_state: AppState,
    fake_router: FakeRouter,
) -> None:
    fake_router.plan_task_result = PlanResponse(
        summary="Step 1: do the thing.\nStep 2: profit."
    )

    await app_presenter.on_plan()

    plan_entries = [e for e in app_state.context_entries if e.label == "📋 Plan"]
    assert len(plan_entries) == 1
    plan = plan_entries[0]
    assert plan.raw_content == fake_router.plan_task_result.summary
    assert plan.content == f"{fake_router.plan_task_result.summary}"
    assert plan.is_loading is False


async def test_plan_with_no_prior_context_uses_instructions_only(
    app_presenter: AppPresenter,
    app_state: AppState,
    fake_router: FakeRouter,
) -> None:
    # build_llm_prompt() always returns at least the USER INSTRUCTIONS section,
    # so plan_task is called even with an empty context panel.
    fake_router.plan_task_result = PlanResponse(summary="build a rocket first")
    app_state.update_instructions("build a rocket")

    expected_prompt = app_state.build_llm_prompt()
    await app_presenter.on_plan()

    assert fake_router.calls == [("plan_task", (expected_prompt,), {})]
    assert "build a rocket" in expected_prompt

    plan_entries = [e for e in app_state.context_entries if e.label == "📋 Plan"]
    assert len(plan_entries) == 1
    assert plan_entries[0].content == "build a rocket first"
    assert plan_entries[0].is_loading is False


async def test_plan_updates_entry_with_error_on_router_failure(
    app_state: AppState,
    fake_router: FakeRouter,
) -> None:
    from app.controller import AppController
    from app.exceptions import AgentError

    class Boom(FakeRouter):
        async def plan_task(self, prompt: str) -> PlanResponse:
            self._record("plan_task", prompt)
            raise AgentError("LLM exploded")

    router = Boom()
    presenter = AppPresenter(app_state, AppController(app_state, router))
    app_state.add_context_entry(
        entry_id="ctx_seed",
        label="Seed",
        content="some context",
        raw_content="some context",
    )

    await presenter.on_plan()

    plan_entries = [e for e in app_state.context_entries if e.label == "📋 Plan"]
    assert len(plan_entries) == 1
    plan = plan_entries[0]
    assert "Plan Error" in plan.content
    assert "LLM exploded" in plan.content
    assert plan.is_loading is False
