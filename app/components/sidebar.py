from dataclasses import dataclass
from typing import Callable

from nicegui import ui

from app.components import icons
from app.events import LoadingChangedPayload
from app.state import AppState


@dataclass
class SidebarView:
    state: AppState
    on_node_click: Callable
    on_refresh: Callable
    on_create_overview: Callable
    on_add_tree: Callable
    on_load_overview: Callable | None = None

    def __post_init__(self) -> None:
        self._expanded: set[str] = set()
        self._refresh_btn = None
        self._overview_btn = None
        self._overview_load_btn = None

        with ui.element("aside").classes("sidebar"):
            self._render_head()
            self._render_panel_head()
            self._render_tree_wrap()
            self._render_overview_btn()

    def _render_head(self) -> None:
        with ui.element("div").classes("sidebar-head"):
            with ui.element("div").classes("sidebar-title"):
                ui.html('<span class="dot"></span>')
                ui.html("<span>nice</span>")
                ui.html('<span class="sidebar-meta">/ coding-agent</span>')

    def _render_panel_head(self) -> None:
        with ui.element("div").classes("panel-head"):
            ui.html('<span class="panel-label">Project files</span>')
            with ui.element("div").classes("panel-actions"):
                self._refresh_btn = ui.element("button").classes("iconbtn")
                with self._refresh_btn:
                    ui.html(icons.refresh())
                self._refresh_btn.on("click", self._handle_refresh)
                add_tree_btn = ui.element("button").classes("iconbtn")
                add_tree_btn.props('title="Add file tree to context"')
                with add_tree_btn:
                    ui.html(icons.add_to_context())
                add_tree_btn.on("click", self._handle_add_tree)

    def _render_overview_btn(self) -> None:
        with ui.element("div").classes("overview-actions"):
            self._overview_btn = (
                ui.element("button")
                .classes("overview-btn")
                .on("click", self.on_create_overview)
            )
            with self._overview_btn:
                with ui.element("span").classes("overview-ic"):
                    ui.html(icons.overview())
                ui.html('<span class="overview-label">Create overview</span>')
                ui.html('<span class="kbd">⌘O</span>')

            self._overview_load_btn = ui.element("button").classes(
                "overview-load-btn"
            )
            self._overview_load_btn.props(
                'type="button" title="Load project overview into context" aria-label="Load project overview into context"'
            )
            with self._overview_load_btn:
                ui.html(icons.add_overview_to_context())
            if self.on_load_overview is not None:
                self._overview_load_btn.on("click", self._handle_load_overview)

    def _render_tree_wrap(self) -> None:
        with ui.element("div").classes("tree-wrap"):
            with ui.element("div").classes("tree"):
                self._render_tree()

    @ui.refreshable
    def _render_tree(self) -> None:
        nodes = self.state.tree_nodes or []
        if not nodes:
            ui.html(
                '<div class="tree-row is-dimmed" style="padding-left:14px">'
                '<span class="tree-name">(empty)</span></div>'
            )
            return
        in_ctx = self._collect_in_ctx_paths()
        for node in nodes:
            self._render_node(node, depth=0, in_ctx=in_ctx)

    def _render_node(self, node: dict, depth: int, in_ctx: set) -> None:
        node_id: str = node["id"]
        label: str = node.get("label", node_id.split("/")[-1])
        is_folder: bool = bool(node.get("is_folder")) or node.get("icon") == "folder"
        is_open = node_id in self._expanded
        is_in_ctx = node_id in in_ctx

        row = ui.element("div").classes("tree-row")
        row.style(f"padding-left: {depth * 14}px")
        if is_in_ctx and not is_folder:
            row.classes(add="is-selected")

        with row:
            chev = ui.element("button").classes("tree-chev")
            chev.props('type="button" aria-label="Toggle folder"')
            with chev:
                if is_folder:
                    ui.html(icons.chevron_right())
            if is_open:
                chev.classes(add="is-open")

            ic_classes = (
                "tree-icon is-folder"
                if is_folder
                else f"tree-icon {icons.file_ext_class(label)}"
            ).strip()
            with ui.element("span").classes(ic_classes):
                ui.html(icons.folder() if is_folder else icons.file_icon())

            ui.html(f'<span class="tree-name">{_escape(label)}</span>')

        row.on(
            "click",
            lambda _e, nid=node_id: self.on_node_click(_NodeClickEvent(nid)),
        )
        if is_folder:
            chev.on("click.stop", lambda _e, nid=node_id: self._toggle_folder(nid))
            if is_open:
                for child in node.get("children") or []:
                    self._render_node(child, depth + 1, in_ctx)

    def _toggle_folder(self, node_id: str) -> None:
        if node_id in self._expanded:
            self._expanded.discard(node_id)
        else:
            self._expanded.add(node_id)
        self._render_tree.refresh()

    def _collect_in_ctx_paths(self) -> set[str]:
        return {entry.id for entry in self.state.context_entries}

    def refresh(self, _payload=None) -> None:
        self._render_tree.refresh()

    def on_context_changed(self, _payload=None) -> None:
        self._render_tree.refresh()

    def on_loading_changed(self, payload: LoadingChangedPayload) -> None:
        if payload.key == "tree" and self._refresh_btn is not None:
            if payload.loading:
                self._refresh_btn.props("disable")
            else:
                self._refresh_btn.props(remove="disable")
        elif payload.key == "create_overview" and self._overview_btn is not None:
            if payload.loading:
                self._overview_btn.classes(add="is-loading")
                self._overview_btn.props("disable")
                if self._overview_load_btn is not None:
                    self._overview_load_btn.props("disable")
            else:
                self._overview_btn.classes(remove="is-loading")
                self._overview_btn.props(remove="disable")
                if self._overview_load_btn is not None:
                    self._overview_load_btn.props(remove="disable")

    def _handle_refresh(self, _e=None):
        result = self.on_refresh()
        if hasattr(result, "__await__"):
            return result
        return None

    def _handle_add_tree(self, _e=None):
        result = self.on_add_tree()
        if hasattr(result, "__await__"):
            return result
        return None

    def _handle_load_overview(self, _e=None):
        if self.on_load_overview is None:
            return None
        result = self.on_load_overview()
        if hasattr(result, "__await__"):
            return result
        return None


@dataclass
class _NodeClickEvent:
    value: str


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
