from dataclasses import dataclass
from typing import Callable, Awaitable

from nicegui import ui


@dataclass
class SkillsView:
    get_skills: Callable[[], Awaitable[list[str]]]
    on_add_skill: Callable[[str], Awaitable[None]]

    def __post_init__(self) -> None:
        self.dialog = ui.dialog()

        with (
            self.dialog,
            ui.card()
            .classes("dialog-card-themed")
            .style("width: 420px; max-height: 80vh;"),
        ):
            with ui.element("div").classes("dialog-head"):
                ui.html(
                    '<span class="dialog-title">'
                    '<span class="dialog-title-glyph">🛠️</span>Skills'
                    "</span>"
                )

            with ui.element("div").classes("dialog-body"):
                self.list_container = ui.element("div").style(
                    "display: flex; flex-direction: column; gap: 6px;"
                )

            with ui.element("div").classes("dialog-foot w-full"):
                close_btn = ui.element("button").classes("cmdbtn")
                with close_btn:
                    ui.html("<span>Close</span>")
                close_btn.on("click", lambda _e: self.dialog.close())

    async def open(self) -> None:
        self.list_container.clear()
        skills = await self.get_skills()
        with self.list_container:
            if not skills:
                ui.html(
                    '<div class="dialog-empty">No skills found in /skills folder.</div>'
                )
            else:
                for skill in skills:
                    btn = ui.element("button").classes("skill-row")
                    with btn:
                        ui.html(
                            '<span class="skill-glyph">›</span>'
                            f"<span>{_escape(skill)}</span>"
                        )
                    btn.on("click", lambda _e, s=skill: self._handle_select(s))
        self.dialog.open()

    async def _handle_select(self, skill: str) -> None:
        await self.on_add_skill(skill)


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
