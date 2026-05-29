import asyncio
from dataclasses import dataclass
from typing import Callable

from nicegui import ui

from app.components import icons
from app.events import LoadingChangedPayload
from app.state import AppState


@dataclass
class PromptDockView:
    state: AppState
    on_update_instructions: Callable
    on_build_context: Callable
    on_create_epic: Callable
    on_load_epic: Callable
    on_load_prd: Callable
    on_plan: Callable
    on_implement: Callable
    on_clear: Callable
    on_copy: Callable

    def __post_init__(self) -> None:
        self._expanded = False
        self._render()

    def _render(self) -> None:
        with ui.element("div").classes("dock"):
            self._dock_inner = ui.element("div").classes("dock-inner")
            with self._dock_inner:
                self._render_input_row()
                self._render_command_row()

    def _render_input_row(self) -> None:
        with ui.element("div").classes("dock-input"):
            ui.html('<span class="dock-prompt-glyph">▸</span>')
            self.instructions = (
                ui.textarea(
                    placeholder="Add instructions, paste an error, or describe a change…",
                )
                .props("borderless dense")
                .classes("w-full")
                .on("keyup", self._on_keyup, throttle=1.0)
                .on("paste", self._on_paste)
                .on("cut", self._on_paste)
                .on("blur", self._on_blur)
            )
            self._expand_btn = ui.element("button").classes("iconbtn dock-expand")
            with self._expand_btn:
                ui.html(icons.diagonal())
            self._expand_btn.on("click", self._toggle_expand)

    def _render_command_row(self) -> None:
        with ui.element("div").classes("dock-row"):
            with ui.element("div").classes("cmd-group cmd-group-l"):
                prd_btn = ui.element("button").classes("ghostbtn")
                prd_btn.props(
                    'title="Load Product Requirements Document (.nice/prd.md)"'
                )
                with prd_btn:
                    ui.html(icons.doc())
                    ui.html("<span>PRD</span>")
                prd_btn.on("click", self.on_load_prd)

                with ui.element("div").classes("epic-cluster"):
                    ui.html('<span class="epic-label">Epic</span>')
                    create_btn = ui.element("button").classes("epic-btn")
                    with create_btn:
                        ui.html(icons.plus())
                        ui.html("<span>Create</span>")
                    create_btn.on("click", self.on_create_epic)

                    load_btn = ui.element("button").classes("epic-btn")
                    with load_btn:
                        ui.html(icons.layers())
                        ui.html("<span>Load</span>")
                    load_btn.on("click", self.on_load_epic)

                ui.html('<span class="util-spacer"></span>')

                copy_btn = ui.element("button").classes("ghostbtn")
                with copy_btn:
                    ui.html(icons.copy())
                    ui.html("<span>Copy all</span>")
                copy_btn.on("click", self.on_copy)

                clear_btn = ui.element("button").classes("ghostbtn")
                with clear_btn:
                    ui.html(icons.trash())
                    ui.html("<span>Clear</span>")
                clear_btn.on("click", self.on_clear)

            with ui.element("div").classes("cmd-group cmd-group-r"):
                self._build_btn = ui.element("button").classes("cmdbtn action-btn")
                with self._build_btn:
                    ui.html(icons.sparkle())
                    ui.html("<span>Build context</span>")
                self._build_btn.on("click", self.on_build_context)

                self._plan_btn = ui.element("button").classes("cmdbtn action-btn")
                with self._plan_btn:
                    ui.html(icons.overview())
                    ui.html("<span>Plan</span>")
                self._plan_btn.on("click", self.on_plan)

                self._implement_btn = ui.element("button").classes(
                    "cmdbtn primary action-btn-impl"
                )
                with self._implement_btn:
                    ui.html(icons.send())
                    ui.html("<span>Implement</span>")
                    ui.html('<span class="kbd">⌘↵</span>')
                self._implement_btn.on("click", self.on_implement)

    def _on_keyup(self, _e=None) -> None:
        self.on_update_instructions(self.instructions.value or "")

    async def _on_paste(self, _e=None) -> None:
        await asyncio.sleep(0.1)
        self.on_update_instructions(self.instructions.value or "")

    def _on_blur(self, _e=None) -> None:
        self.on_update_instructions(self.instructions.value or "")

    def _toggle_expand(self, _e=None) -> None:
        self._expanded = not self._expanded
        if self._expanded:
            self._dock_inner.classes(add="is-expanded")
        else:
            self._dock_inner.classes(remove="is-expanded")

    def on_context_size_changed(self, _payload=None) -> None:
        return

    def on_cost_changed(self, _payload) -> None:
        return

    def on_loading_changed(self, payload: LoadingChangedPayload) -> None:
        if payload.key == "ask_llm":
            if payload.loading:
                pass
            else:
                pass
        elif payload.key == "implement":
            if payload.loading:
                self._implement_btn.classes(add="is-loading")
                self._implement_btn.props("disable")
            else:
                self._implement_btn.classes(remove="is-loading")
                self._implement_btn.props(remove="disable")
        elif payload.key == "plan_task":
            if payload.loading:
                self._plan_btn.classes(add="is-loading")
                self._plan_btn.props("disable")
            else:
                self._plan_btn.classes(remove="is-loading")
                self._plan_btn.props(remove="disable")
        elif payload.key == "build_context":
            if payload.loading:
                self._build_btn.classes(add="is-loading")
                self._build_btn.props("disable")
            else:
                self._build_btn.classes(remove="is-loading")
                self._build_btn.props(remove="disable")
