from typing import Any

from app.events import Events
from app.presenter import AppPresenter, EPIC_PLAN_FILE_NAME
from app.state import AppState
from tests.fakes.fake_router import FakeRouter


async def test_create_epic_populates_state_with_result(
    app_presenter: AppPresenter,
    app_state: AppState,
    fake_router: FakeRouter,
    captured_events: list[tuple[str, Any]],
) -> None:
    fake_router.create_epic_result = "## Epic Plan\n\nStep 1: do the thing."
    app_state.add_context_entry(
        entry_id="ctx_seed",
        label="Seed",
        content="some context",
        raw_content="some context",
    )

    # Capture the prompt before calling — the loading epic entry (is_loading=True) is
    # excluded from get_context(), so the prompt inside on_create_epic matches this.
    expected_prompt = app_state.build_llm_prompt()

    app_state.bus.on(
        Events.CONTEXT_CHANGED, lambda _p: captured_events.append((Events.CONTEXT_CHANGED, _p))
    )

    await app_presenter.on_create_epic()

    assert fake_router.calls == [
        ("create_epic", (expected_prompt,), {}),
        ("get_file_text", (EPIC_PLAN_FILE_NAME,), {}),
    ]

    epic_entries = [e for e in app_state.context_entries if e.label == "🗺️ Epic Plan"]
    assert len(epic_entries) == 1
    epic = epic_entries[0]
    assert epic.is_loading is False
    assert len(captured_events) >= 2


async def test_create_epic_with_no_prior_context_uses_instructions_only(
    app_presenter: AppPresenter,
    app_state: AppState,
    fake_router: FakeRouter,
) -> None:
    # build_llm_prompt() always returns at least the USER INSTRUCTIONS section,
    # so create_epic is called even with an empty context panel.
    fake_router.create_epic_result = "## Epic"
    app_state.update_instructions("build a rocket")

    expected_prompt = app_state.build_llm_prompt()
    await app_presenter.on_create_epic()

    assert fake_router.calls == [
        ("create_epic", (expected_prompt,), {}),
        ("get_file_text", (EPIC_PLAN_FILE_NAME,), {}),
    ]
    assert "build a rocket" in expected_prompt

    epic_entries = [e for e in app_state.context_entries if e.label == "🗺️ Epic Plan"]
    assert len(epic_entries) == 1
    assert epic_entries[0].is_loading is False


async def test_create_epic_updates_entry_with_error_on_router_failure(
    app_state: AppState,
    fake_router: FakeRouter,
) -> None:
    from app.controller import AppController

    class Boom(FakeRouter):
        async def create_epic(self, instructions: str) -> str:
            self._record("create_epic", instructions)
            raise RuntimeError("LLM exploded")

    router = Boom()
    presenter = AppPresenter(app_state, AppController(app_state, router))
    app_state.add_context_entry(
        entry_id="ctx_seed",
        label="Seed",
        content="some context",
        raw_content="some context",
    )

    await presenter.on_create_epic()

    epic_entries = [e for e in app_state.context_entries if e.label == "🗺️ Epic Plan"]
    assert len(epic_entries) == 1
    epic = epic_entries[0]
    assert "Epic Error" in epic.content
    assert "LLM exploded" in epic.content
    assert epic.is_loading is False
