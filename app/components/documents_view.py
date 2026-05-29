from dataclasses import dataclass
from typing import Callable, Awaitable

from nicegui import ui

from core.schemas import SearchResult
from app.components import icons


@dataclass
class DocumentsView:
    on_ingest: Callable[[], Awaitable[str]]
    on_search: Callable[[str], Awaitable[list]]
    on_add_to_context: Callable[[SearchResult], None]

    def __post_init__(self) -> None:
        self.dialog = ui.dialog()

        with (
            self.dialog,
            ui.card()
            .classes("dialog-card-themed")
            .style("width: min(960px, 95vw); max-width: 95vw; max-height: 85vh;"),
        ):
            with ui.element("div").classes("dialog-head"):
                ui.html(
                    '<span class="dialog-title">'
                    '<span class="dialog-title-glyph">📚</span>Documents'
                    "</span>"
                )

            with ui.element("div").classes("dialog-body"):
                ui.html('<span class="dialog-section-label">Ingest</span>')
                ui.html(
                    '<div class="dialog-helper">Ingest documents from the '
                    "<code>rag/documents</code> folder into the vector store.</div>"
                )

                self.status_area = ui.element("div")

                with ui.element("div").classes("dialog-row"):
                    self.ingest_btn = ui.element("button").classes("cmdbtn ingest")
                    with self.ingest_btn:
                        ui.html(icons.layers())
                        self._ingest_label = ui.html("<span>Ingest</span>")
                    self.ingest_btn.on("click", lambda _e: self._handle_ingest())

                ui.html('<div class="dialog-divider"></div>')

                ui.html('<span class="dialog-section-label">Search Documents</span>')
                with ui.element("div").classes("dialog-row"):
                    self.search_input = (
                        ui.input(placeholder="Enter search query…")
                        .classes("dialog-input")
                        .style("flex: 1;")
                        .props("borderless dense")
                    )
                    self.search_btn = ui.element("button").classes("cmdbtn primary")
                    with self.search_btn:
                        self._search_label = ui.html("<span>Search</span>")
                    self.search_btn.on("click", lambda _e: self._handle_search())

                self.search_results_area = ui.element("div").style("width: 100%;")

            with ui.element("div").classes("dialog-foot"):
                close_btn = ui.element("button").classes("cmdbtn")
                with close_btn:
                    ui.html("<span>Close</span>")
                close_btn.on("click", lambda _e: self.dialog.close())

    def open(self) -> None:
        self._show_idle()
        self.dialog.open()

    def _show_idle(self) -> None:
        self.status_area.clear()
        with self.status_area:
            ui.html('<div class="dialog-status-msg">Ready to ingest documents.</div>')

    def _show_loading(self) -> None:
        self.status_area.clear()
        with self.status_area:
            with ui.row().classes("justify-center w-full").style("padding: 8px 0;"):
                ui.spinner(size="md").style("color: var(--c-accent);")

    def _show_completed(self, report: str) -> None:
        self.status_area.clear()
        with self.status_area:
            ui.html('<div class="dialog-status-ok">✓ Completed</div>')
            with (
                ui.element("div")
                .classes("card-body card-body-text")
                .style(
                    "max-height: 220px; overflow: auto; border-radius: var(--r-1); margin-top: 6px;"
                )
            ):
                ui.markdown(report)

    def _show_error(self, error: str) -> None:
        self.status_area.clear()
        with self.status_area:
            ui.html('<div class="dialog-status-err">✗ Failed</div>')
            ui.html(
                f'<div class="dialog-helper" style="color: var(--c-red);">'
                f"{_escape(error)}</div>"
            )

    async def _handle_ingest(self) -> None:
        self._set_btn_state(self.ingest_btn, self._ingest_label, "Ingesting…", True)
        self._show_loading()

        try:
            report = await self.on_ingest()
            self._show_completed(report)
        except Exception as exc:
            self._show_error(str(exc))
        finally:
            self._set_btn_state(self.ingest_btn, self._ingest_label, "Ingest", False)

    def _show_search_loading(self) -> None:
        self.search_results_area.clear()
        with self.search_results_area:
            with ui.row().classes("justify-center w-full").style("padding: 12px 0;"):
                ui.spinner(size="md").style("color: var(--c-accent);")

    def _show_search_results(self, results: list[SearchResult]) -> None:
        self.search_results_area.clear()
        with self.search_results_area:
            if not results:
                ui.html('<div class="dialog-empty">No results found.</div>')
                return

            ui.html(
                f'<div class="dialog-status-count">{len(results)} '
                f"result(s) found</div>"
            )
            for result in results:
                with ui.element("div").classes("search-result"):
                    with ui.element("div").classes("search-result-head"):
                        ui.html(
                            f'<span class="search-result-source">'
                            f"{_escape(result.source)}</span>"
                        )
                        ui.html(
                            f'<span class="search-result-score">'
                            f"score: {result.score:.4f}</span>"
                        )
                        add_btn = (
                            ui.element("button")
                            .classes("cmdbtn primary")
                            .style("flex-shrink: 0; white-space: nowrap;")
                        )
                        with add_btn:
                            ui.html("<span>+ Context</span>")
                        add_btn.on(
                            "click",
                            lambda _e, r=result: self._handle_add_to_context(r),
                        )
                    with ui.expansion("Show content", icon="article"):
                        ui.html(
                            f'<div class="search-result-content">'
                            f"{_escape(result.content)}</div>"
                        )

    def _show_search_error(self, error: str) -> None:
        self.search_results_area.clear()
        with self.search_results_area:
            ui.html('<div class="dialog-status-err">✗ Search failed</div>')
            ui.html(
                f'<div class="dialog-helper" style="color: var(--c-red);">'
                f"{_escape(error)}</div>"
            )

    def _handle_add_to_context(self, result: SearchResult) -> None:
        self.on_add_to_context(result)

    async def _handle_search(self) -> None:
        query = self.search_input.value.strip()
        if not query:
            ui.notify("Please enter a search query.", type="warning")
            return

        self._set_btn_state(self.search_btn, self._search_label, "Searching…", True)
        self._show_search_loading()

        try:
            results = await self.on_search(query)
            self._show_search_results(results)
        except Exception as exc:
            self._show_search_error(str(exc))
        finally:
            self._set_btn_state(self.search_btn, self._search_label, "Search", False)

    @staticmethod
    def _set_btn_state(btn, label, text: str, disabled: bool) -> None:
        label.set_content(f"<span>{text}</span>")
        if disabled:
            btn.classes(add="is-disabled")
        else:
            btn.classes(remove="is-disabled")


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
