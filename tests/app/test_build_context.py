from typing import Any

import pytest

from core.schemas import ContentType, ContextItem
from app.events import Events
from app.presenter import AppPresenter
import app.presenter as presenter_mod
from app.state import AppState
from app.controller import AppController
from tests.fakes.fake_router import FakeRouter


async def test_build_context_populates_state_with_returned_items(
    app_presenter: AppPresenter,
    app_state: AppState,
    fake_router: FakeRouter,
    captured_events: list[tuple[str, Any]],
) -> None:
    fake_router.build_context_result = [
        ContextItem(title="src/foo.py", content="print('hi')", type=ContentType.file),
        ContextItem(title="my_skill.md", content="do X", type=ContentType.skill),
        ContextItem(title="Notes", content="free-form", type=ContentType.general),
    ]
    app_state.update_instructions("refactor foo")

    app_state.bus.on(
        Events.CONTEXT_CHANGED,
        lambda _p: captured_events.append((Events.CONTEXT_CHANGED, _p)),
    )

    await app_presenter.on_build_context()

    assert fake_router.calls == [("build_context", ("refactor foo",), {})]

    ids = [e.id for e in app_state.context_entries]
    labels = [e.label for e in app_state.context_entries]
    assert ids == ["src/foo.py", "skill_my_skill.md", ids[2]]
    assert ids[2].startswith("ctx_")
    assert labels == ["📄 src/foo.py", "🛠️ my_skill.md", "Notes"]

    file_entry, skill_entry, general_entry = app_state.context_entries
    assert file_entry.raw_content == "print('hi')"
    assert file_entry.content == "```py\nprint('hi')\n```"
    assert file_entry.editable is False
    assert skill_entry.raw_content == "do X"
    assert "**Skill: my_skill.md**" in skill_entry.content
    assert skill_entry.editable is False
    assert general_entry.editable is True
    assert general_entry.raw_content == "free-form"

    # Loading placeholder added then removed; final 3 items added → at least 5 emissions.
    assert len(captured_events) >= 5


async def test_build_context_removes_loading_placeholder_on_error(
    monkeypatch: pytest.MonkeyPatch,
    app_presenter: AppPresenter,
    app_state: AppState,
    fake_router: FakeRouter,
) -> None:
    class Boom(FakeRouter):
        async def build_context(self, instructions: str) -> list[ContextItem]:
            self._record("build_context", instructions)
            raise RuntimeError("upstream exploded")

    router = Boom()

    presenter = AppPresenter(app_state, AppController(app_state, router))

    notified: list = []
    monkeypatch.setattr(
        presenter_mod.ui, "notify", lambda *a, **kw: notified.append((a, kw))
    )

    await presenter.on_build_context()

    assert app_state.context_entries == []
    assert notified and "Build context failed" in notified[0][0][0]
