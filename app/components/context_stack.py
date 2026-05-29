from dataclasses import dataclass
from typing import Awaitable, Callable

from nicegui import ui

from app.components.context_card import ContextCardView
from app.state import AppState


@dataclass
class ContextStackView:
    state: AppState
    on_remove: Callable[[str], None]
    on_update: Callable[[str, str], None]
    on_summarize: Callable[[str], Awaitable[None]]

    def __post_init__(self) -> None:
        self._last_count = 0

    def render(self) -> None:
        self._render_content()

    @ui.refreshable
    def _render_content(self) -> None:
        entries = self.state.context_entries
        if not entries:
            ui.html(
                '<div style="color:var(--c-fg-3);font-size:11.5px;'
                'padding:6px 2px;font-family:var(--font-mono)">'
                "No context yet — pick a file from the sidebar or use the chips below."
                "</div>"
            )
        else:
            in_ctx = {entry.id for entry in entries}
            for entry in entries:
                ContextCardView(
                    entry=entry,
                    on_remove=self.on_remove,
                    on_update=self.on_update,
                    on_summarize=self.on_summarize,
                    on_after_change=self._render_content.refresh,
                    in_ctx_ids=in_ctx,
                )

        grew = len(entries) > self._last_count
        self._last_count = len(entries)

        scroll_js = (
            "const el = document.querySelector('.stack-body');"
            "if (el) {"
            "el.scrollTop = el.scrollHeight;"
            "requestAnimationFrame(() => { el.scrollTop = el.scrollHeight; });"
            "setTimeout(() => { el.scrollTop = el.scrollHeight; }, 200);"
            "setTimeout(() => { el.scrollTop = el.scrollHeight; }, 500);"
            "}"
            if grew
            else ""
        )
        ui.run_javascript(
            "setTimeout(() => {"
            "window.applyLineNumbersAll && window.applyLineNumbersAll();"
            f"{scroll_js}"
            "}, 50);"
        )

    def refresh(self, _payload=None) -> None:
        self._render_content.refresh()
