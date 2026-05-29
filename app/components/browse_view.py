from dataclasses import dataclass
from typing import Callable, Awaitable

from nicegui import ui

from app.components import icons

_PLACEHOLDER = (
    "Inspect a running web page. Examples:\n"
    "• Open http://localhost:8080 and tell me what the bottom-left button does\n"
    "• Extract the pricing tiers from example.com/pricing\n"
    "• Debug why the login button doesn't respond on staging.myapp.com"
)


@dataclass
class BrowseView:
    on_browse: Callable[[str], Awaitable[None]]

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
                    f'<span class="dialog-title">'
                    f'<span class="dialog-title-glyph">{icons.eye()}</span>Inspect'
                    "</span>"
                )

            with ui.element("div").classes("dialog-body w-full"):
                self.instruction_input = (
                    ui.textarea(placeholder=_PLACEHOLDER)
                    .classes("dialog-input dialog-textarea w-full")
                    .props("borderless autofocus rows=8")
                )

            with ui.element("div").classes("dialog-foot w-full"):
                cancel_btn = ui.element("button").classes("cmdbtn")
                with cancel_btn:
                    ui.html("<span>Cancel</span>")
                cancel_btn.on("click", lambda _e: self.dialog.close())

                self.ask_btn = ui.element("button").classes("cmdbtn primary")
                with self.ask_btn:
                    ui.html("<span>Execute</span>")
                self.ask_btn.on("click", lambda _e: self._handle_browse())

    def open(self) -> None:
        self.instruction_input.set_value("")
        self.dialog.open()

    async def _handle_browse(self) -> None:
        instruction = self.instruction_input.value.strip()
        if not instruction:
            ui.notify("Please enter instructions.", type="warning")
            return

        self.dialog.close()
        await self.on_browse(instruction)
