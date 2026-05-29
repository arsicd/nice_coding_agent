from dataclasses import dataclass, field
from typing import Callable, Awaitable
import re

from nicegui import ui

from app.components import icons
from app.models.context_entry import ContextEntry
from lib.helpers import context_size

_LANG_MAP = {
    "py": "python",
    "ts": "typescript",
    "tsx": "typescript",
    "js": "javascript",
    "jsx": "javascript",
    "mjs": "javascript",
    "cjs": "javascript",
    "md": "markdown",
    "yaml": "yaml",
    "yml": "yaml",
    "toml": "ini",
    "json": "json",
    "sh": "bash",
    "bash": "bash",
    "zsh": "bash",
    "html": "xml",
    "xml": "xml",
    "css": "css",
    "sql": "sql",
    "rs": "rust",
    "go": "go",
    "java": "java",
    "kt": "kotlin",
    "rb": "ruby",
    "c": "c",
    "h": "c",
    "cpp": "cpp",
    "hpp": "cpp",
}


@dataclass
class ContextCardView:
    entry: ContextEntry
    on_remove: Callable[[str], None]
    on_update: Callable[[str, str], None]
    on_summarize: Callable
    on_after_change: Callable[[], Awaitable[None]]
    in_ctx_ids: frozenset[str] | set[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        self._render()

    def _render(self) -> None:
        e = self.entry
        classes = "card"
        if e.is_minimized:
            classes += " is-min"
        if e.pinned:
            classes += " is-pinned"
        if e.is_loading:
            classes += " is-active"

        with ui.element("div").classes(classes):
            self._render_head()
            if not e.is_minimized:
                self._render_body()

    def _render_head(self) -> None:
        e = self.entry
        head = ui.element("div").classes("card-head")
        head.on("click", lambda _e: self._toggle_minimize())
        with head:
            with ui.element("div").classes("card-head-l"):
                self._render_path_and_icon()
                tok_count = context_size(e.content or e.raw_content or "")
                ui.html(f'<span class="card-meta">{tok_count:,} tok</span>')

            with ui.element("div").classes("card-head-r"):
                if e.is_loading:
                    ui.html('<span class="status-dot"></span>')
                if e.editable and not e.is_loading and (e.content or e.raw_content):
                    btn = ui.element("button").classes("iconbtn")
                    with btn:
                        ui.html(icons.sparkle())
                    btn.on(
                        "click.stop",
                        lambda _e, eid=e.id: self.on_summarize(eid),
                    )
                if e.editable and e.render_as_markdown and not e.is_loading:
                    edit_btn = ui.element("button").classes("iconbtn")
                    with edit_btn:
                        ui.html(icons.edit())
                    edit_btn.on("click.stop", lambda _e: self._toggle_editing())

                pin_classes = "iconbtn is-on" if e.pinned else "iconbtn"
                pin_btn = ui.element("button").classes(pin_classes)
                with pin_btn:
                    ui.html(icons.pin())
                pin_btn.on("click.stop", lambda _e: self._toggle_pin())

                close_btn = ui.element("button").classes("iconbtn")
                with close_btn:
                    ui.html(icons.close())
                close_btn.on("click.stop", lambda _e, eid=e.id: self.on_remove(eid))

    def _render_path_and_icon(self) -> None:
        e = self.entry
        if e.is_file_entry():
            path = e.file_path_from_label()
            ext_class = icons.file_ext_class(path.split("/")[-1]) or "generic"
            with ui.element("span").classes(f"card-ic {ext_class}"):
                ui.html(icons.file_icon())
            self._render_path_segments(path)
        else:
            with ui.element("span").classes("card-ic generic"):
                ui.html(icons.doc())
            ui.html(f'<span class="path-leaf">{_escape(e.label)}</span>')

    def _render_path_segments(self, path: str) -> None:
        parts = path.split("/")
        with ui.element("span").classes("card-path"):
            if len(parts) == 1:
                ui.html(f'<span class="path-leaf">{_escape(parts[0])}</span>')
                return
            for dir_part in parts[:-1]:
                ui.html(f'<span class="path-dir">{_escape(dir_part)}</span>')
                ui.html('<span class="path-sep">/</span>')
            ui.html(f'<span class="path-leaf">{_escape(parts[-1])}</span>')

    def _render_body(self) -> None:
        e = self.entry
        if e.is_loading:
            with ui.element("div").classes("card-body card-body-text"):
                ui.spinner("dots").style("color: var(--c-accent)")
            return
        if e.is_editing:
            self._render_editor()
        elif e.render_as_markdown:
            self._render_markdown_body()
        elif e.editable:
            self._render_editor()
        elif e.is_file_entry():
            self._render_code_body()
        else:
            self._render_markdown_body()

    def _render_code_body(self) -> None:
        e = self.entry
        raw = e.raw_content or self._strip_fence(e.content)
        ext = e.file_extension()
        lang = _LANG_MAP.get(ext, ext or "text")
        with ui.element("div").classes("card-body"):
            ui.code(raw, language=lang).classes("hljs-themed w-full")

    def _render_markdown_body(self) -> None:
        e = self.entry
        with ui.element("div").classes("card-body card-body-text"):
            ui.markdown(e.content or "")

    def _render_editor(self) -> None:
        e = self.entry
        initial = e.raw_content if e.raw_content else e.content
        with ui.element("div").classes("card-body card-body-edit"):
            ui.textarea(
                value=initial,
                placeholder="Type or paste content here…",
            ).props("autogrow borderless dense").classes("w-full").on(
                "blur",
                lambda ev, eid=e.id: self._save_edit(eid, ev.sender.value),
            )

    @staticmethod
    def _strip_fence(content: str) -> str:
        if not content.startswith("```"):
            return content
        lines = content.split("\n")
        body = lines[1:]
        if body and body[-1].strip() == "```":
            body = body[:-1]
        return "\n".join(body)

    def _toggle_minimize(self) -> None:
        self.entry.is_minimized = not self.entry.is_minimized
        self.on_after_change()

    def _toggle_pin(self) -> None:
        self.entry.pinned = not self.entry.pinned
        self.on_after_change()

    def _toggle_editing(self) -> None:
        self.entry.is_editing = not self.entry.is_editing
        self.on_after_change()

    def _save_edit(self, entry_id: str, value: str) -> None:
        self.entry.is_editing = False
        self.on_update(entry_id, value)


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
