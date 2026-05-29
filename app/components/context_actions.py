from dataclasses import dataclass
from typing import Callable

from nicegui import ui

from app.components import icons


@dataclass
class ContextActions:
    on_add_additional: Callable
    on_open_skills: Callable
    on_open_ask: Callable
    on_open_browse: Callable
    on_open_search: Callable
    on_open_docs: Callable | None

    def render(self) -> None:
        with ui.element("div").classes("context-actions"):
            self._chip(
                "add-card primary-add chip-research",
                icons.sparkle(),
                "Research",
                on_click=self.on_open_ask,
            )
            self._chip(
                "add-card primary-add chip-inspect",
                icons.eye(),
                "Inspect",
                on_click=self.on_open_browse,
            )
            self._chip(
                "add-card primary-add chip-web",
                icons.web(),
                "Web search",
                on_click=self.on_open_search,
            )
            ui.element("div").classes("chip-group-divider")
            self._chip(
                "add-card chip-skill",
                icons.skill(),
                "Skill",
                on_click=self.on_open_skills,
            )
            if self.on_open_docs:
                self._chip(
                    "add-card chip-docs",
                    icons.doc(),
                    "Docs",
                    on_click=self.on_open_docs,
                )
            self._chip(
                "add-card chip-custom",
                icons.plus(),
                "Custom",
                kbd="⌘K",
                on_click=self.on_add_additional,
            )

    @staticmethod
    def _chip(
        classes: str,
        icon_html: str,
        label: str,
        on_click: Callable,
        kbd: str | None = None,
    ) -> None:
        btn = ui.element("button").classes(classes)
        with btn:
            ui.html(icon_html)
            ui.html(f"<span>{label}</span>")
            if kbd:
                ui.html(f'<span class="kbd">{kbd}</span>')
        btn.on("click", on_click)
