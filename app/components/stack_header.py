from dataclasses import dataclass
from typing import Awaitable, Callable

from nicegui import ui

from app.components import icons
from app.events import CostChangedPayload
from app.state import AppState
from lib.helpers import context_size

_SUGGESTED_MAX = 32_000
_DANGER_THRESHOLD = 100_000


@dataclass
class StackHeaderView:
    state: AppState
    on_model_mode_change: Callable
    on_settings_click: Callable[[], Awaitable[None]]
    _high: bool = True

    def __post_init__(self) -> None:
        with ui.element("header").classes("stack-head"):
            with ui.element("div").classes("stack-head-l"):
                ui.html('<span class="stack-title">Context</span>')
                self._entries_label = ui.label("0 entries").classes("stack-meta")
                ui.html('<span class="head-divider"></span>')
                with ui.element("div").classes("meter"):
                    with ui.element("div").classes("meter-bar"):
                        self._meter_fill = (
                            ui.element("span").classes("meter-fill").style("width:0%")
                        )
                    self._meter_num = ui.label("0").classes("meter-num")
                    ui.html('<span class="meter-unit">tok</span>')

            with ui.element("div").classes("stack-head-r"):
                self._cost_label = ui.label("$0.0000").classes("meter-cost")
                ui.html('<span class="head-divider"></span>')
                self._toggle = (
                    ui.element("div")
                    .classes("hi-toggle")
                    .classes("is-on" if self._high else "")
                    .on("click", self._toggle_high_standard)
                )
                with self._toggle:
                    with ui.element("span").classes("hi-box"):
                        ui.html(icons.check())
                    ui.html(icons.bolt())
                    self._toggle_label = ui.label("High" if self._high else "Standard")
                ui.html('<span class="head-divider"></span>')
                settings_btn = ui.element("button").classes("iconbtn")
                with settings_btn:
                    ui.html(icons.settings())
                settings_btn.on("click", self.on_settings_click)

        self._update_meter()

    def on_context_changed(self, _payload=None) -> None:
        self._update_meter()

    def on_cost_changed(self, payload: CostChangedPayload) -> None:
        self._cost_label.set_text(f"${payload.cost:.4f}")

    def _update_meter(self) -> None:
        tokens = self._compute_tokens()
        pct = min(100.0, tokens / _SUGGESTED_MAX * 100)
        self._meter_fill.style(f"width:{pct:.1f}%")
        if tokens >= _DANGER_THRESHOLD:
            self._meter_fill.classes(add="is-danger", remove="is-warn is-ok")
        elif tokens >= _SUGGESTED_MAX:
            self._meter_fill.classes(add="is-warn", remove="is-danger is-ok")
        else:
            self._meter_fill.classes(add="is-ok", remove="is-warn is-danger")
        self._meter_num.set_text(f"{tokens:,}")
        count = len(self.state.context_entries)
        self._entries_label.set_text(f"{count} {'entry' if count == 1 else 'entries'}")

    def _compute_tokens(self) -> int:
        try:
            return self.state.context_size()
        except Exception:
            combined = "\n".join(e.content or "" for e in self.state.context_entries)
            combined += "\n" + (self.state.instructions or "")
            return context_size(combined)

    async def _toggle_high_standard(self) -> None:
        self._high = not self._high
        await self.on_model_mode_change("high" if self._high else "standard")
        self._update_model_mode_display()

    def _update_model_mode_display(self):
        if self._high:
            self._toggle.classes(add="is-on")
            self._toggle_label.set_text("High")
        else:
            self._toggle.classes(remove="is-on")
            self._toggle_label.set_text("Standard")

    def on_model_mode_sync(self, payload: str) -> None:
        is_high = payload == "high"
        if self._high != is_high:
            self._high = is_high
            self._update_model_mode_display()
