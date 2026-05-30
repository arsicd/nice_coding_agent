from dataclasses import dataclass
from typing import Callable, Awaitable

from nicegui import ui


@dataclass
class SettingsView:
    load_settings: Callable[[], Awaitable[str]]
    save_settings: Callable[[str], Awaitable[None]]

    def __post_init__(self) -> None:
        self.dialog = ui.dialog()

        with (
            self.dialog,
            ui.card()
            .classes("dialog-card-themed")
            .style("width: 520px; max-height: 80vh;"),
        ):
            with ui.element("div").classes("dialog-head"):
                ui.html(
                    '<span class="dialog-title">'
                    '<span class="dialog-title-glyph">⚙️</span>Settings'
                    "</span>"
                )

            with ui.element("div").classes("dialog-body"):
                self.textarea = ui.textarea().classes("dialog-input dialog-textarea")
                self.textarea.props("rows=20")

            with ui.element("div").classes("dialog-foot w-full"):
                close_btn = ui.element("button").classes("cmdbtn")
                with close_btn:
                    ui.html("<span>Close</span>")
                close_btn.on("click", lambda _e: self.dialog.close())

                save_btn = ui.element("button").classes("cmdbtn primary")
                with save_btn:
                    ui.html("<span>Save</span>")
                save_btn.on("click", lambda _e: self._on_save())

    async def open(self) -> None:
        try:
            text = await self.load_settings()
            self.textarea.set_value(text)
        except Exception as exc:
            ui.notify(f"Failed to load settings: {exc}", type="negative")
        self.dialog.open()

    async def _on_save(self) -> None:
        try:
            value = self.textarea.value
            await self.save_settings(value)
            self.dialog.close()
        except Exception as exc:
            ui.notify(f"Failed to save settings: {exc}", type="negative")
