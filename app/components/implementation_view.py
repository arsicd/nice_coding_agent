from dataclasses import dataclass
from typing import Awaitable, Callable

from nicegui import ui

from app.events import ImplementationPayload
from core.schemas import CodeChange, CodeChangeResponse


@dataclass
class ImplementationView:
    on_close: Callable
    on_apply: Callable[[CodeChange], Awaitable[None]]

    def __post_init__(self) -> None:
        self._render()

    def _render(self):
        self.dialog = (
            ui.dialog()
            .props("full-width full-height")
            .classes("impl-dialog-wrap")
            .on("hide", self.on_close)
        )

        with (
            self.dialog,
            ui.card()
            .classes("dialog-card-themed impl-dialog")
            .style("width: 100%; height: 100%;"),
        ):
            with ui.element("div").classes("dialog-head"):
                ui.html(
                    '<span class="dialog-title">'
                    '<span class="dialog-title-glyph">✨</span>Implementation'
                    "</span>"
                )
                close_btn = ui.element("button").classes("cmdbtn impl-close-btn")
                with close_btn:
                    ui.html("<span>Close</span>")
                close_btn.on("click", lambda _e: self.dialog.close())

            with ui.element("div").classes("dialog-body impl-body"):
                self.md_area = ui.element("div").classes("impl-markdown")
                with self.md_area:
                    self.md = ui.markdown("")

                self.cards_area = ui.element("div").classes("impl-cards-area")
                self.cards_area.set_visibility(False)

    def on_implementation_changed(self, payload: ImplementationPayload) -> None:
        if payload.status == "thinking":
            self._show_markdown()
            self.md.set_content("*Thinking...*")
            self.dialog.close()
            return

        if payload.status == "error":
            self._show_markdown()
            self.md.set_content(f"❌ {payload.error or 'Unknown error'}")
            self.dialog.open()
            return

        if payload.response is None:
            self.dialog.close()
            return

        if not payload.response.changes:
            self._show_markdown()
            self.md.set_content(payload.response.summary)
            self.dialog.open()
            return

        self._show_cards()
        self._render_structured(payload.response)
        self.dialog.open()

    def _show_markdown(self) -> None:
        self.md_area.set_visibility(True)
        self.cards_area.set_visibility(False)

    def _show_cards(self) -> None:
        self.md_area.set_visibility(False)
        self.cards_area.set_visibility(True)

    def _render_structured(self, response: CodeChangeResponse) -> None:
        self.cards_area.clear()
        with self.cards_area:
            with ui.element("div").classes("impl-summary"):
                ui.html('<span class="dialog-section-label">Summary</span>')
                ui.label(response.summary).classes("impl-summary-text")
                ui.html(
                    f'<span class="impl-count">'
                    f"{len(response.changes)} change"
                    f"{'s' if len(response.changes) != 1 else ''} suggested"
                    "</span>"
                )

            for i, change in enumerate(response.changes, start=1):
                self._render_change_card(i, change)

    def _render_change_card(self, index: int, change: CodeChange) -> None:
        with ui.element("div").classes("impl-card"):
            with ui.element("div").classes("impl-card-head"):
                with ui.element("div").classes("impl-card-meta"):
                    with ui.element("div").classes("impl-card-title-row"):
                        ui.label(f"#{index}").classes("impl-card-index")
                        ui.label(change.description).classes("impl-card-title")
                    with ui.element("div").classes("impl-card-path"):
                        ui.label("📄").classes("impl-card-path-glyph")
                        ui.label(change.file_path).classes("impl-card-path-text")

                apply_btn = ui.element("button").classes(
                    "cmdbtn primary impl-apply-btn"
                )
                with apply_btn:
                    ui.html("<span>Apply</span>")
                apply_btn.on(
                    "click",
                    lambda _e, c=change, btn=apply_btn: self._handle_apply(c, btn),
                )

            with ui.expansion("Show diff", icon="code").classes("impl-diff-expansion"):
                with ui.element("div").classes("impl-diff-grid"):
                    with ui.element("div").classes("impl-diff-col"):
                        ui.html(
                            '<span class="impl-diff-label impl-diff-label-old">Before</span>'
                        )
                        ui.code(change.old_text, language="python").classes(
                            "impl-diff-code"
                        )
                    with ui.element("div").classes("impl-diff-col"):
                        ui.html(
                            '<span class="impl-diff-label impl-diff-label-new">After</span>'
                        )
                        ui.code(change.new_text, language="python").classes(
                            "impl-diff-code"
                        )

    async def _handle_apply(self, change: CodeChange, btn) -> None:
        btn.classes(add="is-disabled")
        btn.clear()
        with btn:
            ui.html("<span>Applying…</span>")
        try:
            await self.on_apply(change)
            btn.clear()
            with btn:
                ui.html("<span>Applied ✓</span>")
            btn.classes(remove="primary", add="is-applied")
        except Exception as exc:
            btn.classes(remove="is-disabled")
            btn.clear()
            with btn:
                ui.html("<span>Apply</span>")
            ui.notify(f"Failed: {exc}", type="negative", timeout=5000)
