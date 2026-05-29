from dataclasses import dataclass
from typing import Callable, Awaitable

from nicegui import ui

_PLACEHOLDER = (
    "Research (default) digs through the codebase, web, and documents to answer.\n"
    "Ask sends a single LLM call with no codebase or other context.\n"
    "Examples:\n"
    "• What does this codebase use for authentication?\n"
    "• Summarize the differences between FastAPI and Flask for our use case\n"
    "• Research best practices for caching LLM responses in production"
)


@dataclass
class AskLlmView:
    on_ask: Callable[[str], Awaitable[None]]
    on_research: Callable[[str], Awaitable[None]]

    def __post_init__(self):
        self.dialog = ui.dialog()

        with (
            self.dialog,
            ui.card()
            .classes("dialog-card-themed")
            .style("width: 90vw; max-width: 1200px; max-height: 90vh;"),
        ):
            with ui.element("div").classes("dialog-head w-full"):
                ui.html(
                    '<span class="dialog-title">'
                    '<span class="dialog-title-glyph">💬</span>Research</span>'
                )

            with ui.element("div").classes("dialog-body w-full"):
                self.question_input = (
                    ui.textarea(placeholder=_PLACEHOLDER)
                    .classes("dialog-input dialog-textarea w-full")
                    .props("borderless autofocus rows=8")
                )

            with ui.element("div").classes("dialog-foot w-full"):
                cancel_btn = ui.element("button").classes("cmdbtn")
                with cancel_btn:
                    ui.html("<span>Cancel</span>")
                cancel_btn.on("click", lambda _e: self.dialog.close())

                self.ask_btn = ui.element("button").classes("cmdbtn")
                with self.ask_btn:
                    ui.html("<span>Ask</span>")
                self.ask_btn.on("click", lambda _e: self._handle_ask())

                self.research_btn = ui.element("button").classes("cmdbtn primary")
                with self.research_btn:
                    ui.html("<span>Research</span>")
                self.research_btn.on("click", lambda _e: self._handle_research())

    def open(self) -> None:
        self.question_input.set_value("")
        self.dialog.open()

    async def _handle_ask(self) -> None:
        question = self.question_input.value.strip()
        if not question:
            ui.notify("Please enter a question.", type="warning")
            return

        self.dialog.close()
        await self.on_ask(question)

    async def _handle_research(self) -> None:
        question = self.question_input.value.strip()
        if not question:
            ui.notify("Please enter a question.", type="warning")
            return

        self.dialog.close()
        await self.on_research(question)
