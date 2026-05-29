import time
from typing import Callable, Awaitable

from nicegui import ui

from app.components import icons
from app.state import AppState
from core.schemas import StreamEvent, StreamKind
from lib.helpers import context_size

REFRESH_INTERVAL = 0.5


class StreamView:
    def __init__(
        self,
        state: AppState,
        on_cancel: Callable[[], Awaitable[None]] | None = None,
    ):
        self._state = state
        self._on_cancel_callback = on_cancel

        self._collapsed = True
        self._reasoning_collapsed = False
        self._active = False
        self._dirty = False
        self._dialog_open = False

        self._stream_start = None
        self._reasoning_secs = None

        self._tok_cache = {"r_len": -1, "r_tok": 0, "t_len": -1, "t_tok": 0}

        self._is_rendered = False
        self._pending: list[tuple[str, object, float]] = []

        self._container = None
        self._status = None
        self._status_text = None
        self._meta = None
        self._tail = None
        self._reasoning_card = None
        self._reasoning_dur = None
        self._reasoning_tok = None
        self._reasoning_label = None
        self._response_section = None
        self._text_label = None
        self._dialog = None
        self._dialog_reasoning = None
        self._dialog_text = None
        self._cancel_btn = None

    def render(self) -> None:
        with ui.element("div").classes("stream-view is-collapsed") as container:
            self._container = container
            self._render_head()
            self._render_body()
        self._build_dialog()

        ui.timer(REFRESH_INTERVAL, self._flush_if_dirty)

        self._is_rendered = True
        pending, self._pending = self._pending, []
        for kind, payload, ts in pending:
            self._handle_chunk(payload, ts)

    def _render_head(self) -> None:
        head = ui.element("div").classes("stream-head")
        head.on("click", lambda _e: self._toggle_collapsed())
        with head:
            with ui.element("div").classes("stream-head-l"):
                with ui.element("span").classes("stream-chevron"):
                    ui.html(icons.chevron_right())
                ui.html('<span class="stream-title">Console</span>')
                with ui.element("span").classes("stream-status") as status:
                    self._status = status
                    ui.element("span").classes("stream-status-dot")
                    self._status_text = ui.label("IDLE").classes("stream-status-text")
                self._meta = ui.label("").classes("stream-meta")
                self._tail = ui.label("").classes("stream-tail")

            with ui.element("div").classes("stream-head-r"):
                cancel = ui.element("button").classes("iconbtn stream-cancel")
                with cancel:
                    ui.html(icons.stop())
                cancel.on("click.stop", lambda _e: self._on_cancel())
                cancel.set_visibility(self._active)
                self._cancel_btn = cancel

                expand = ui.element("button").classes("iconbtn stream-expand")
                with expand:
                    ui.html(icons.diagonal())
                expand.on("click.stop", lambda _e: self._open_dialog())

            ui.element("span").classes("stream-progress")

    def _render_body(self) -> None:
        with ui.element("div").classes("stream-body"):
            card = ui.element("div").classes("reasoning-card")
            self._reasoning_card = card
            with card:
                rhead = ui.element("div").classes("reasoning-head")
                rhead.on("click", lambda _e: self._toggle_reasoning())
                with rhead:
                    with ui.element("div").classes("reasoning-head-l"):
                        with ui.element("span").classes("reasoning-chevron"):
                            ui.html(icons.chevron_right())
                        ui.icon("psychology").classes("reasoning-ic")
                        ui.html('<span class="reasoning-title">Reasoning</span>')
                        self._reasoning_dur = ui.label("").classes("reasoning-sub")
                    self._reasoning_tok = ui.label("").classes("reasoning-tok")
                with ui.element("div").classes("reasoning-body"):
                    self._reasoning_label = ui.markdown("")

            section = ui.element("div").classes("stream-response")
            self._response_section = section
            with section:
                with ui.element("div").classes("stream-response-head"):
                    ui.element("span").classes("stream-response-dot")
                    ui.label("RESPONSE").classes("stream-response-label")
                with ui.element("div").classes("stream-response-body"):
                    self._text_label = ui.markdown("")

        card.set_visibility(False)
        section.set_visibility(False)

    def _build_dialog(self) -> None:
        with ui.dialog().props("maximized") as dialog:
            self._dialog = dialog
            with ui.element("div").classes("stream-dialog"):
                with ui.element("div").classes("stream-dialog-head"):
                    ui.html('<span class="stream-title">Console</span>')
                    close = ui.element("button").classes("iconbtn")
                    with close:
                        ui.html(icons.close())
                    close.on("click", lambda _e: dialog.close())
                with ui.element("div").classes("stream-dialog-body"):
                    ui.html('<div class="stream-dialog-label">Reasoning</div>')
                    self._dialog_reasoning = ui.markdown("")
                    ui.html('<div class="stream-dialog-label">Response</div>')
                    self._dialog_text = ui.markdown("")
        dialog.on("hide", lambda _e: self._set_dialog_open(False))

    def on_stream_chunk(self, event: StreamEvent) -> None:
        ts = time.monotonic()
        if not self._is_rendered:
            self._pending.append(("chunk", event, ts))
            return
        self._handle_chunk(event, ts)

    def _handle_chunk(self, event: StreamEvent, ts: float) -> None:
        if (
            event.kind == StreamKind.TEXT
            and self._reasoning_secs is None
            and self._stream_start is not None
            and self._state.stream_reasoning
        ):
            self._reasoning_secs = max(1, round(ts - self._stream_start))
        self._dirty = True

    def on_stream_start(self, event: StreamEvent):
        ts = time.monotonic()
        self._state.clear_stream()
        self._reset_tok_cache()
        self._active = True
        self._stream_start = ts
        self._reasoning_secs = None
        self._dirty = True
        self._container.classes(add="stream-active", remove="stream-done")
        self._set_status("writing")
        if event.can_stop:
            self._cancel_btn.set_visibility(True)
        self._flush_if_dirty()

    def on_stream_end(self, _: StreamEvent):
        ts = time.monotonic()
        self._active = False
        if (
            self._reasoning_secs is None
            and self._stream_start is not None
            and self._state.stream_reasoning
        ):
            self._reasoning_secs = max(1, round(ts - self._stream_start))
        self._dirty = True
        self._container.classes(add="stream-done", remove="stream-active")
        self._set_status("done")
        self._cancel_btn.set_visibility(False)
        self._flush_if_dirty()

    def _toggle_collapsed(self) -> None:
        self._collapsed = not self._collapsed
        if self._container:
            if self._collapsed:
                self._container.classes(add="is-collapsed")
            else:
                self._container.classes(remove="is-collapsed")

    def _toggle_reasoning(self) -> None:
        self._reasoning_collapsed = not self._reasoning_collapsed
        if self._reasoning_card:
            if self._reasoning_collapsed:
                self._reasoning_card.classes(add="is-collapsed")
            else:
                self._reasoning_card.classes(remove="is-collapsed")

    async def _on_cancel(self) -> None:
        if self._on_cancel_callback:
            await self._on_cancel_callback()

    def _open_dialog(self) -> None:
        self._dialog_open = True
        if self._dialog_reasoning:
            self._dialog_reasoning.set_content(self._state.stream_reasoning)
        if self._dialog_text:
            self._dialog_text.set_content(self._state.stream_text)
        if self._dialog:
            self._dialog.open()

    def _set_dialog_open(self, value: bool) -> None:
        self._dialog_open = value

    def _set_status(self, state: str) -> None:
        if not self._status or not self._status_text:
            return
        if state == "writing":
            self._status.classes(add="is-writing", remove="is-done")
            self._status_text.set_text("WRITING")
        elif state == "done":
            self._status.classes(add="is-done", remove="is-writing")
            self._status_text.set_text("DONE")
        else:
            self._status.classes(remove="is-writing is-done")
            self._status_text.set_text("IDLE")

    def _reset_tok_cache(self) -> None:
        self._tok_cache["r_len"] = -1
        self._tok_cache["r_tok"] = 0
        self._tok_cache["t_len"] = -1
        self._tok_cache["t_tok"] = 0

    def _count_tokens(self, s: str, which: str) -> int:
        key_len = f"{which}_len"
        key_tok = f"{which}_tok"
        n = len(s) if s else 0
        if n == self._tok_cache[key_len]:
            return self._tok_cache[key_tok]
        tok = context_size(s) if s else 0
        self._tok_cache[key_len] = n
        self._tok_cache[key_tok] = tok
        return tok

    def _flush_if_dirty(self) -> None:
        if not self._dirty:
            return
        if not self._is_rendered:
            return
        self._dirty = False

        text = self._state.stream_text
        reasoning = self._state.stream_reasoning

        self._text_label.set_content(text)
        self._reasoning_label.set_content(reasoning)
        self._reasoning_card.set_visibility(bool(reasoning))
        self._response_section.set_visibility(bool(text))

        r_tok = self._count_tokens(reasoning, "r")
        t_tok = self._count_tokens(text, "t")
        self._update_meta(r_tok, t_tok)
        self._reasoning_tok.set_text(f"{r_tok:,} t" if r_tok else "")
        if self._reasoning_secs is not None:
            self._reasoning_dur.set_text(f"· thought for {self._reasoning_secs}s")
        elif self._active and reasoning:
            self._reasoning_dur.set_text("· thinking…")
        else:
            self._reasoning_dur.set_text("")
        self._tail.set_text(self._tail_text(text, reasoning))

        if self._dialog_open:
            self._dialog_reasoning.set_content(reasoning)
            self._dialog_text.set_content(text)

    def _update_meta(self, r_tok: int, t_tok: int) -> None:
        parts = []
        if r_tok:
            parts.append(f"{r_tok:,} reasoning")
        if t_tok:
            parts.append(f"{t_tok:,} response")
        self._meta.set_text((" + ".join(parts) + " tok") if parts else "")

    @staticmethod
    def _tail_text(text: str, reasoning: str) -> str:
        src = (text or reasoning).strip()
        if not src:
            return ""
        return src.splitlines()[-1][-200:]
