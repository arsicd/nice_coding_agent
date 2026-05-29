from dataclasses import dataclass
from typing import Callable, Awaitable

from nicegui import ui


@dataclass
class WebSearchView:
    on_search: Callable[[str], Awaitable[None]]

    def __post_init__(self) -> None:
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
                    '<span class="dialog-title-glyph">🔍</span>Web Search'
                    "</span>"
                )

            with ui.element("div").classes("dialog-body w-full"):
                self.query_input = (
                    ui.input(placeholder="Enter search query…")
                    .classes("dialog-input w-full text-lg")
                    .props("borderless autofocus")
                )

            with ui.element("div").classes("dialog-foot w-full"):
                cancel_btn = ui.element("button").classes("cmdbtn")
                with cancel_btn:
                    ui.html("<span>Cancel</span>")
                cancel_btn.on("click", lambda _e: self.dialog.close())

                self.submit_btn = ui.element("button").classes("cmdbtn primary")
                with self.submit_btn:
                    self._submit_label = ui.html("<span>Search</span>")
                self.submit_btn.on("click", lambda _e: self._handle_search())

    def open(self) -> None:
        self.query_input.set_value("")
        self._submit_label.set_content("<span>Search</span>")
        self.dialog.open()

    async def _handle_search(self) -> None:
        query = self.query_input.value.strip()
        if not query:
            ui.notify("Please enter a search query.", type="warning")
            return

        self._submit_label.set_content("<span>Searching…</span>")
        self.dialog.close()
        await self.on_search(query)
