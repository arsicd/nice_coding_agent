#### `app/components/ask_llm_view.py`
- **Role**: view
- **Purpose**: Displays a dialog for asking or researching questions and triggers the provided callbacks.
- **Depends on**: nicegui
- **Structure**:
class AskLlmView
  def __post_init__(self):
  def open(self) -> None:
  async def _handle_ask(self) -> None:
  async def _handle_research(self) -> None:

#### `app/components/browse_view.py`
- **Role**: view
- **Purpose**: Render a dialog UI that collects user instructions and triggers browsing actions.
- **Depends on**: nicegui, app.components.icons
- **Structure**:
class BrowseView
  def __post_init__(self):
  def open(self) -> None:
  async def _handle_browse(self) -> None:

#### `app/components/context_actions.py`
- **Role**: view
- **Purpose**: Renders a set of interactive chips for context actions, delegating click handlers to configured callbacks.
- **Depends on**: nicegui, app.components.icons
- **Structure**:
class ContextActions
  def render(self) -> None:
  def _chip(classes: str, icon_html: str, label: str, on_click: Callable, kbd: str | None = None) -> None:

#### `app/components/context_card.py`
- **Role**: view
- **Purpose**: Render a UI card that displays context entry details, supports editing, pinning, and summarization, and triggers callbacks for removal and updates.
- **Depends on**: nicegui, lib.helpers, app.models.context_entry, app.components.icons
- **Structure**:
class ContextCardView
  def __post_init__(self) -> None:
  def _render(self) -> None:
  def _render_head(self) -> None:
  def _render_path_and_icon(self) -> None:
  def _render_path_segments(self, path: str) -> None:
  def _render_body(self) -> None:
  def _render_code_body(self) -> None:
  def _render_markdown_body(self) -> None:
  def _render_editor(self) -> None:
  def _strip_fence(content: str) -> str:
  def _toggle_minimize(self) -> None:
  def _toggle_pin(self) -> None:
  def _toggle_editing(self) -> None:
  def _save_edit(self, entry_id: str, value: str) -> None:
def _escape(text: str) -> str:

#### `app/components/context_stack.py`
- **Role**: view
- **Purpose**: Renders a dynamic stack of context cards reflecting the current application context and updates the UI when context entries change.
- **Depends on**: nicegui, app.components.context_card, app.state
- **Structure**:
class ContextStackView
  def __post_init__(self) -> None:
  def render(self) -> None:
  def _render_content(self) -> None:
  def refresh(self, _payload=None) -> None:

#### `app/components/documents_view.py`
- **Role**: view
- **Purpose**: Displays a dialog for ingesting documents and performing search queries, coordinating UI state and delegating actions to service callbacks.
- **Depends on**: nicegui, core.schemas, app.components.icons
- **Structure**:
class DocumentsView
  def __post_init__(self) -> None:
  def open(self) -> None:
  def _show_idle(self) -> None:
  def _show_loading(self) -> None:
  def _show_completed(self, report: str) -> None:
  def _show_error(self, error: str) -> None:
  async def _handle_ingest(self) -> None:
  def _show_search_loading(self) -> None:
  def _show_search_results(self, results: list[SearchResult]) -> None:
  def _show_search_error(self, error: str) -> None:
  def _handle_add_to_context(self, result: SearchResult) -> None:
  async def _handle_search(self) -> None:
  def _set_btn_state(btn, label, text: str, disabled: bool) -> None:
def _escape(text: str) -> str:

#### `app/components/icons.py`
- **Role**: view
- **Purpose**: Render SVG icons for UI components using currentColor styling.
- **Depends on**: none
- **Structure**:
def chevron_right(size: int = 10) -> str:
def folder(size: int = 13) -> str:
def file_icon(size: int = 13) -> str:
def plus(size: int = 12) -> str:
def minus(size: int = 12) -> str:
def maximize(size: int = 12) -> str:
def close(size: int = 12) -> str:
def pin(size: int = 12) -> str:
def refresh(size: int = 13) -> str:
def collapse(size: int = 13) -> str:
def add_to_context(size: int = 13) -> str:
def add_overview_to_context(size: int = 13) -> str:
def search(size: int = 13) -> str:
def sparkle(size: int = 13) -> str:
def edit(size: int = 13) -> str:
def doc(size: int = 13) -> str:
def tools(size: int = 13) -> str:
def chat(size: int = 13) -> str:
def overview(size: int = 13) -> str:
def layers(size: int = 13) -> str:
def check(size: int = 11) -> str:
def bolt(size: int = 12) -> str:
def settings(size: int = 13) -> str:
def branch(size: int = 12) -> str:
def send(size: int = 13) -> str:
def copy(size: int = 12) -> str:
def trash(size: int = 12) -> str:
def diagonal(size: int = 11) -> str:
def stop(size: int = 11) -> str:
def bug(size: int = 13) -> str:
def eye(size: int = 13) -> str:
def web(size: int = 13) -> str:
def skill(size: int = 13) -> str:
def file_ext_class(name: str) -> str:

#### `app/components/implementation_view.py`
- **Role**: view
- **Purpose**: Renders and manages a dialog for visualizing implementation changes and handling user apply actions.
- **Depends on**: nicegui, app.events, core.schemas
- **Structure**:
class ImplementationView
  def __post_init__(self) -> None:
  def _render(self):
  def on_implementation_changed(self, payload: ImplementationPayload) -> None:
  def _show_markdown(self) -> None:
  def _show_cards(self) -> None:
  def _render_structured(self, response: CodeChangeResponse) -> None:
  def _render_change_card(self, index: int, change: CodeChange) -> None:
  async def _handle_apply(self, change: CodeChange, btn) -> None:

#### `app/components/prompt_dock.py`
- **Role**: view
- **Purpose**: Manages the prompt dock UI, handling user input and dispatching callbacks.
- **Depends on**: nicegui, app.components.icons, app.events, app.state
- **Structure**:
class PromptDockView
  def __post_init__(self) -> None:
  def _render(self) -> None:
  def _render_input_row(self) -> None:
  def _render_command_row(self) -> None:
  def _on_keyup(self, _e=None) -> None:
  async def _on_paste(self, _e=None) -> None:
  def _on_blur(self, _e=None) -> None:
  def _toggle_expand(self, _e=None) -> None:
  def on_context_size_changed(self, _payload=None) -> None:
  def on_cost_changed(self, _payload) -> None:
  def on_loading_changed(self, payload: LoadingChangedPayload) -> None:

#### `app/components/settings_view.py`
- **Role**: view
- **Purpose**: Displays a settings dialog and coordinates loading and saving of settings.
- **Depends on**: nicegui
- **Structure**:
class SettingsView
  def __post_init__(self) -> None:
  async def open(self) -> None:
  async def _on_save(self) -> None:

#### `app/components/sidebar.py`
- **Role**: view
- **Purpose**: Renders the application's sidebar navigation and handles user interactions with the file tree.
- **Depends on**: nicegui, app.components.icons, app.events.LoadingChangedPayload, app.state.AppState
- **Structure**:
class SidebarView
  def __post_init__(self) -> None:
  def _render_head(self) -> None:
  def _render_panel_head(self) -> None:
  def _render_overview_btn(self) -> None:
  def _render_tree_wrap(self) -> None:
  def _render_tree(self) -> None:
  def _render_node(self, node: dict, depth: int, in_ctx: set) -> None:
  def _toggle_folder(self, node_id: str) -> None:
  def _collect_in_ctx_paths(self) -> set[str]:
  def refresh(self, _payload=None) -> None:
  def on_context_changed(self, _payload=None) -> None:
  def on_loading_changed(self, payload: LoadingChangedPayload) -> None:
  def _handle_refresh(self, _e=None):
  def _handle_add_tree(self, _e=None):
  def _handle_load_overview(self, _e=None):
class _NodeClickEvent
def _escape(text: str) -> str:

#### `app/components/skills_view.py`
- **Role**: view
- **Purpose**: Render a dialog displaying available skills and handle user selection to add a skill.
- **Depends on**: nicegui
- **Structure**:
class SkillsView
  def __post_init__(self) -> None:
  async def open(self) -> None:
  async def _handle_select(self, skill: str) -> None:
def _escape(text: str) -> str:

#### `app/components/stack_header.py`
- **Role**: view
- **Purpose**: Renders the stack header UI and updates the token meter based on context and cost changes. Handles user interactions for model mode toggling and settings.
- **Depends on**: nicegui.ui, app.state.AppState, app.events.CostChangedPayload, lib.helpers.context_size, app.components.icons
- **Structure**:
class StackHeaderView
  def __post_init__(self) -> None:
  def on_context_changed(self, _payload=None) -> None:
  def on_cost_changed(self, payload: CostChangedPayload) -> None:
  def _update_meter(self) -> None:
  def _compute_tokens(self) -> int:
  async def _toggle_high_standard(self) -> None:
  def _update_model_mode_display(self):
  def on_model_mode_sync(self, payload: str) -> None:

#### `app/components/stream_view.py`
- **Role**: view
- **Purpose**: Render the streaming console UI, manage its state, and handle user interactions such as cancel, expand, and reasoning toggles.
- **Depends on**: nicegui, app.components.icons, app.state, core.schemas, lib.helpers
- **Structure**:
class StreamView
  def __init__(self, state: AppState, on_cancel: Callable[[], Awaitable[None]] | None = None):
  def render(self) -> None:
  def _render_head(self) -> None:
  def _render_body(self) -> None:
  def _build_dialog(self) -> None:
  def on_stream_chunk(self, event: StreamEvent) -> None:
  def _handle_chunk(self, event: StreamEvent, ts: float) -> None:
  def on_stream_start(self, event: StreamEvent):
  def on_stream_end(self, _: StreamEvent):
  def _toggle_collapsed(self) -> None:
  def _toggle_reasoning(self) -> None:
  async def _on_cancel(self) -> None:
  def _open_dialog(self) -> None:
  def _set_dialog_open(self, value: bool) -> None:
  def _set_status(self, state: str) -> None:
  def _reset_tok_cache(self) -> None:
  def _count_tokens(self, s: str, which: str) -> int:
  def _flush_if_dirty(self) -> None:
  def _update_meta(self, r_tok: int, t_tok: int) -> None:
  def _tail_text(text: str, reasoning: str) -> str:

#### `app/components/web_search_view.py`
- **Role**: view- **Purpose**: Render a search dialog and invoke a callback when a query is submitted.
- **Depends on**: nicegui
- **Structure**:
class WebSearchView
  def __post_init__(self) -> None:
  def open(self) -> None:
  async def _handle_search(self) -> None:

#### `app/models/context_entry.py`
- **Role**: domain logic
- **Purpose**: Represents a context entry with metadata and provides utilities to infer file properties such as extension and markdown formatting.
- **Depends on**: none
- **Structure**:
class ContextEntry
  def is_file_entry(self) -> bool:
  def file_path_from_label(self) -> str:
  def file_extension(self) -> str:
  def file_content_md(self, raw_content: str) -> str:

#### `app/static/styles.css`
- **Role**: view
- **Purpose**: Provides dark IDE theme styling for the application UI.
- **Depends on**: none

#### `app/controller.py`
- **Role**: glue
- **Purpose**: Coordinates high‑level agent workflows by delegating to the router and managing application state.
- **Depends on**: lib.logger, core.schemas, lib.tree_parser, app.router, app.state, app.exceptions
- **Structure**:
class AppController
  async def set_model_mode(self, mode: str) -> None:
  async def implement_task(self) -> CodeChangeResponse:
  async def plan_task(self) -> PlanResponse:
  async def apply_code_change(self, change: CodeChange) -> None:
  async def summarize_context_item(self, entry_id: str) -> str:
  async def run_documents_ingestion(self) -> str:
  async def search_documents(self, query: str, k: int = 4) -> list[SearchResult]:
  async def web_search(self, query: str) -> str:
  async def ask_llm(self, question: str) -> str:
  async def research(self, question: str) -> str:
  async def browse(self, instruction: str) -> str:
  async def list_skills(self) -> list[str]:
  async def get_skill_content(self, filename: str) -> str:
  async def get_total_cost(self) -> float:
  async def build_context(self) -> list[ContextItem]:
  async def create_overview(self) -> str:
  async def create_epic(self, instructions: str) -> str:
  async def load_file_tree(self) -> None:
  async def is_index_empty(self) -> bool:
  async def fetch_file_content(self, node_id: str) -> str:
  def collect_files_under_folder(self, folder_path: str) -> list[str]:
  def get_tree_node(self, node_id: str) -> dict | None:
  def format_tree_as_text(self) -> str:
  async def reload_context_files(self) -> None:
  async def reset_cost(self):
  async def sync_model_mode(self):
  async def cancel_llm_execution(self) -> None:
  async def config_validation_errors(self) -> str | None:
  async def get_settings_text(self) -> str:
  async def save_settings_text(self, content: str) -> None:

#### `app/events.py`
- **Role**: infrastructure
- **Purpose**: Manages event emission and subscription across the application, defining payload types and an async-capable event bus.
- **Depends on**: core.schemas, lib.logger
- **Structure**:
class LoadingChangedPayload
class LLMStateChangedPayload
class ContextChangedPayload
class CostChangedPayload
class TreeLoadedPayload
class EventBus
  def __init__(self) -> None:
  def on(self, event: str, handler: Handler) -> None:
  def off(self, event: str, handler: Handler) -> None:
  def emit(self, event: str, payload: Any = None) -> None:
  async def emit_async(self, event: str, payload: Any = None) -> None:
  def clear(self, event: str | None = None) -> None:
class ImplementationPayload
class Events

#### `app/exceptions.py`
- **Role**: utility
- **Purpose**: Define custom exception hierarchy used throughout the codebase.
- **Depends on**: none
- **Structure**:
class AppError
class MCPError
class FileReadError
  def __init__(self, path: str, cause: Exception | None = None):
class DirectoryTreeError
class AgentError
class EmptyContextError
  def __init__(self):

#### `app/main.py`
- **Role**: entry point
- **Purpose**: Runs the application, configures routes, initializes state, and launches the UI server.
- **Depends on**: nicegui, fastapi, pydantic.error_wrappers, core.config.settings, core.mcp_server.mcp_server, core.mcp_server.sse_transport, core.container.get_container, app.controller.AppController, app.events.Events, app.presenter.AppPresenter, app.router.Router, app.state.AppState, app.theme.apply_theme, lib.logger.get_logger, search.db.database.ensure_schema_migrated
- **Structure**:
async def sse_endpoint(request: Request):
async def messages_endpoint(request: Request):
async def acquire_slot(client: Client) -> bool:
def show_blocked() -> None:
async def validate_config(controller: AppController, settings_view: SettingsView ) -> None:
async def index(client: Client) -> None:
def main():

#### `app/presenter.py`
- **Role**: glue
- **Purpose**: Coordinates UI interactions and delegates business logic to the controller.
- **Depends on**: nicegui, core.schemas, app.controller, app.events, app.exceptions, app.state, lib.logger
- **Structure**:
class AppPresenter
  async def on_model_mode_change(self, mode: str) -> None:
  async def on_cancel_llm(self) -> None:
  async def get_skills(self) -> list[str]:
  async def get_settings_text(self) -> str:
  async def on_save_settings(self, content: str) -> None:
  async def on_add_skill(self, filename: str) -> None:
  async def on_implement(self) -> None:
  async def on_plan(self) -> None:
  async def on_apply_change(self, change: CodeChange) -> None:
  def on_remove_implementation(self) -> None:
  async def on_summarize_entry(self, entry_id: str) -> None:
  def on_update_context_entry(self, entry_id: str, new_raw: str) -> None:
  async def on_copy_all(self) -> None:
  def on_clear_context(self) -> None:
  def on_remove_context_entry(self, entry_id: str) -> None:
  def on_update_instructions(self, instructions: str) -> None:
  async def on_open_file_path(self, path: str) -> None:
  async def on_node_click(self, e) -> None:
  async def _fetch_and_render(self, file_path: str, is_minimized: bool = True ) -> None:
  async def on_ask_llm(self, question: str) -> None:
  async def on_research(self, question: str) -> None:
  async def on_browse(self, instruction: str) -> None:
  async def on_web_search(self, query: str) -> None:
  async def on_documents_ingest(self) -> str:
  async def on_documents_search(self, query: str) -> list[SearchResult]:
  def on_add_document_to_context(self, result: SearchResult) -> None:
  async def on_add_additional_context(self) -> None:
  async def on_build_context(self) -> None:
  async def on_create_overview(self) -> None:
  async def on_create_epic(self) -> None:
  async def on_load_epic(self) -> None:
  async def on_load_prd(self) -> None:
  async def on_load_overview(self) -> None:
  async def on_load_tree(self) -> None:
  async def load_agents_file(self) -> None:
  async def check_first_run(self):
  async def on_add_tree_to_context(self) -> None:
  async def _loading(self, key: str):

#### `app/router.py`
- **Role**: glue
- **Purpose**: Coordinates routing of LLM‑driven actions by delegating to core router functions.
- **Depends on**: core.router, core.container, core.schemas
- **Structure**:
class IRouter
  async def build_context(self, instructions: str) -> list[ContextItem]:
  async def plan_task(self, prompt: str) -> PlanResponse:
  async def implement_task(self, prompt: str) -> CodeChangeResponse:
  async def create_epic(self, instructions: str) -> str:
  async def create_overview(self) -> str:
  async def summarize_context_item(self, content: str, instructions: str) -> str:
  async def ask_llm(self, question: str) -> str:
  async def research(self, question: str) -> str:
  async def browse(self, instruction: str) -> str:
  async def web_search(self, query: str) -> str:
  async def get_file_text(self, path: str) -> str:
  async def get_ignore_list(self) -> list[str]:
  async def create_file(self, path: str, content: str) -> None:
  async def replace_text_in_file(self, path: str, old_text: str, new_text: str ) -> None:
  async def list_directory_tree(self) -> str:
  async def is_index_empty(self) -> bool:
  async def run_ingestion(self) -> str:
  async def search_documents(self, query: str, k: int = 4) -> list[SearchResult]:
  async def set_model_mode(self, mode: str) -> None:
  async def list_skills(self) -> list[str]:
  async def get_skill_content(self, filename: str) -> str:
  async def get_total_cost(self) -> float:
  async def reset_cost(self) -> float:
  async def get_model_mode(self) -> str:
  async def cancel_llm_execution(self):
  async def config_validation_errors(self) -> str | None:
  async def get_settings_text(self) -> str:
  async def save_settings_text(self, content: str) -> None:
class Router
  def __init__(self, container: AgentContainer | None = None) -> None:
  async def build_context(self, instructions: str) -> list[ContextItem]:
  async def plan_task(self, prompt: str) -> PlanResponse:
  async def implement_task(self, prompt: str) -> CodeChangeResponse:
  async def create_epic(self, instructions: str) -> str:
  async def create_overview(self) -> str:
  async def summarize_context_item(self, content: str, instructions: str) -> str:
  async def ask_llm(self, question: str) -> str:
  async def research(self, question: str) -> str:
  async def browse(self, instruction: str) -> str:
  async def web_search(self, query: str) -> str:
  async def get_file_text(self, path: str) -> str:
  async def get_ignore_list(self) -> list[str]:
  async def create_file(self, path: str, content: str) -> None:
  async def replace_text_in_file(self, path: str, old_text: str, new_text: str ) -> None:
  async def list_directory_tree(self) -> str:
  async def is_index_empty(self) -> bool:
  async def run_ingestion(self) -> str:
  async def search_documents(self, query: str, k: int = 4) -> list[SearchResult]:
  async def set_model_mode(self, mode: str) -> None:
  async def list_skills(self) -> list[str]:
  async def get_skill_content(self, filename: str) -> str:
  async def get_total_cost(self) -> float:
  async def reset_cost(self) -> float:
  async def get_model_mode(self) -> str:
  async def cancel_llm_execution(self):
  async def config_validation_errors(self) -> str | None:
  async def get_settings_text(self) -> str:
  async def save_settings_text(self, content: str) -> None:

#### `app/state.py`
- **Role**: domain logic
- **Purpose**: Manages application-wide state and emits domain events to coordinate UI and model interactions.
- **Depends on**: EventBus, Events, ContextEntry, StateInfo, CodeChangeResponse, StreamEvent, StreamKind, tiktoken, core.schemas, lib.helpers, ContextChangedPayload, LoadingChangedPayload, TreeLoadedPayload, CostChangedPayload
- **Structure**:
class AppState
  def __post_init__(self) -> None:
  def update_instructions(self, instructions: str) -> None:
  def set_model_mode(self, mode: str) -> None:
  def set_loading(self, key: str, value: bool) -> None:
  def set_cost(self, cost: float) -> None:
  def is_loading(self, key: str) -> bool:
  def tree_nodes(self) -> list[dict]:
  def tree_nodes(self, value: list[dict]) -> None:
  def tree_loaded(self) -> bool:
  def tree_loaded(self, value: bool) -> None:
  def get_context_entry(self, entry_id: str) -> ContextEntry | None:
  def add_context_entry(self, entry_id: str, label: str, content: str = "", raw_content: str = "", is_loading: bool = False, editable: bool = True, is_minimized: bool = False, pinned: bool = False, render_as_markdown: bool = False) -> ContextEntry:
  def update_context_entry(self, entry_id: str, content: str, raw_content: str = "", is_loading: bool = False, is_minimized: bool = False, render_as_markdown: bool | None = None) -> None:
  def get_context(self) -> list[str]:
  def build_llm_prompt(self) -> str:
  def state_info(self) -> StateInfo:
  def remove_context_entry(self, entry_id: str) -> None:
  def clear_context(self) -> None:
  def context_size(self) -> int:
  def on_stream_event(self, event: StreamEvent) -> None:
  def clear_stream(self) -> None:

#### `app/theme.py`
- **Role**: glue
- **Purpose**: Add CSS styles and JavaScript for line numbers and docking area to the NiceGUI UI.
- **Depends on**: nicegui
- **Structure**:
def apply_theme():

#### `core/mcp_clients/filesystem/local_filesystem_client.py`
- **Role**: domain logic
- **Purpose**: Manages local filesystem interactions for the MCP client, including file reading, writing, directory listing, and ignore handling.
- **Depends on**: core.mcp_clients.filesystem.mcp_client_base.FilesystemMcpClient, core.config.settings, lib.logger.get_logger, pathspec
- **Structure**:
class LocalFileSystemClient
  def __post_init__(self):
  def _set_ignore_spec(self):
  def _should_ignore(self, path: Path) -> bool:
  async def get_file_text(self, path: str) -> str:
  async def list_directory_tree(self) -> str:
  def _build_tree(self, tree_lines: list[str], current_path: Path, prefix: str = ""):
  async def create_file(self, path: str, content: str) -> str:
  async def replace_text_in_file(self, path: str, old_text: str, new_text: str ) -> str:

#### `core/mcp_clients/filesystem/mcp_client_base.py`
- **Role**: infrastructure
- **Purpose**: Defines the abstract interface for filesystem operations used by MCP clients, outlining methods for reading, listing, replacing text, and creating files.
- **Depends on**: none
- **Structure**:
class FilesystemMcpClient
  async def get_file_text(self, path: str) -> str:
  async def list_directory_tree(self) -> str:
  async def replace_text_in_file(self, path: str, old_text: str, new_text: str ) -> str:
  async def create_file(self, path: str, content: str) -> str:

#### `core/mcp_clients/filesystem/mcp_client_jetbrains.py`
- **Role**: infrastructure
- **Purpose**: Manages persistent MCP session reconnection and provides filesystem operations (read, list, replace, create) to JetBrains IDE via the Model Control Protocol.
- **Depends on**: mcp, core.mcp_clients.filesystem.mcp_client_base, lib.logger, core.config, core.exceptions, JetBrains MCP server
- **Structure**:
class _SessionManager
  def __init__(self) -> None:
  async def get_session(self) -> ClientSession:
  async def _connect(self) -> ClientSession:
  async def reconnect(self) -> ClientSession:
  async def close(self) -> None:
  async def _close_unsafe(self) -> None:
async def get_session() -> ClientSession:
async def close_session() -> None:
async def _call_tool(tool_name: str, arguments: dict) -> str:
class McpClientJetbrains
  async def get_file_text(self, path: str) -> str:
  async def list_directory_tree(self) -> str:
  async def replace_text_in_file(self, path: str, old_text: str, new_text: str ) -> str:
  async def create_file(self, path: str, content: str) -> str:

#### `core/prompts/ask_llm_system_prompt.md`
- **Role**: config
- **Purpose**: Answer user questions concisely and accurately, providing clear code examples when needed.
- **Depends on**: none

#### `core/prompts/browse_system_prompt.md`
- **Role**: glue
- **Purpose**: Drive a real browser via Playwright MCP tools to accomplish a user task.
- **Depends on**: none

{{INVESTIGATE_FILE}}
core/prompts/build_context_prompt.md

{{SEARCH_CODE}}
build_context_prompt

{{INCLUDE_IN_CONTEXT}}
["core/prompts/build_context_prompt.md"]

---
phase_count: 0
shared_contracts: []
unseen_files: []
---

## 1. Executive Summary

## 2. Project Structure Changes

## 3. Architecture & Contracts

## 4. Implementation Phases

## 5. Cross-Cutting Risks

#### `core/prompts/epic_plan_system_prompt.md`
- **Role**: config
- **Purpose**: Define the structure and requirements for generating an Epic Plan in Markdown format.
- **Depends on**: none

#### `core/prompts/file_overview_prompt.md`
- **Role**: config
- **Purpose**: Unclear: file contains no actionable description; only structural placeholder
- **Depends on**: none

{
  "summary": "No changes applied; file remains empty.",
  "changes": []
}

Files to touch:
- core/prompts/implementation_investigate_prompt.md – will replace the empty content with a detailed investigation prompt.

Per-file anchor sketch:
- core/prompts/implementation_investigate_prompt.md: the file currently has 0 lines; we will write starting at line 1 a new prompt that enumerates investigation steps, dependencies, and verification tasks, effectively overwriting the entire file.

Open questions or blockers:
- Unclear what exact scope of investigation is expected (e.g., which module or component to examine) and whether any length or formatting constraints apply.

{
  "summary": "No changes required; the file core/prompts/implementation_review_prompt.md already exists and is empty.",
  "changes": []
}

#### `core/prompts/index_search_prompt.md`
- **Role**: domain logic
- **Purpose**: defines the prompt used to query index search functionality
- **Depends on**: none

**Project Summary**  
The system provides AI‑driven prompt merging and overview generation to help developers and analysts synthesize and explore large language model interactions. It is built with Python, FastAPI, Pydantic, and integrates both open‑source and commercial model providers.

**Architecture**  
The architecture consists of four stable layers: a thin HTTP API layer, an application/service layer that orchestrates prompt merging, a domain layer that encapsulates the merging logic and strategy selection, and an infrastructure layer that handles model communication, configuration, and persistence. Input flows from an HTTP request through the API layer, into the service layer, which delegates to the domain logic, queries external model providers, and returns a synthesized overview response.

**Subsystem Map**

| Module | Responsibility | Anchor Entry Points |
|--------|----------------|---------------------|
| `prompt_engine` | Defines and validates prompt templates and merging strategies | `core/prompt_engine/__init__.py` |
| `merge_service` | Executes the prompt‑merging workflow and selects strategies | `core/merge_service/main.py` |
| `api_gateway` | Exposes REST endpoints for external clients | `api/router.py` |
| `model_adapter` | Wraps external model providers (OpenAI, HuggingFace) | `inference/model_adapter.py` |
| `config_manager` | Loads and validates configuration from env/YAML files | `config/settings.py` |
| `data_store` | Persists user preferences and generated overviews | `data/store.py` |
| `testing` | Holds unit and integration test suites | `tests/unit/` |

**Key Concepts**  
- PromptTemplate  
- MergeStrategy  
- ContextWindow  
- ModelProvider  
- Config  

**Architectural Constraints & Integrations**  
- Depends on external model endpoints (OpenAI, HuggingFace Inference API).  
- Persists data in PostgreSQL.  
- Deployed as Docker containers on Kubernetes.  
- API is stateless and versioned via URL path.  
- Configuration is immutable after startup and sourced from environment variables and YAML files.

### 1. Analysis
No draft plan was provided for review.

### 2. Affected Files

### 3. Execution Steps

### 4. Risks

get_file_text(path: "core/prompts/planning_system_prompt.md")

#### `core/prompts/research_system_prompt.md`
- **Role**: config
- **Purpose**: Define the system-level instructions and behavior for the Research Assistant, guiding its responses and workflow.
- **Depends on**: none

#### `core/prompts/summarization_system_prompt.md`
- **Role**: domain logic
- **Purpose**: Summarize the provided context concisely, preserving essential technical details.
- **Depends on**: none

#### `core/sandbox/profiles/readonly.sb`
- **Role**: config
- **Purpose**: Enforces a read‑only sandbox profile that permits only basic process operations and denies all writes except to designated scratch and system resources.
- **Depends on**: none

#### `core/sandbox/__init__.py`
- **Role**: glue
- **Purpose**: Creates and returns an appropriate sandbox instance for the given project and language by selecting a backend based on the host OS.
- **Depends on**: core.sandbox.base, core.sandbox.macos
- **Structure**:
def make_sandbox(project_root: Path, language: str, **kwargs) -> Sandbox:

#### `core/sandbox/base.py`
- **Role**: domain logic
- **Purpose**: Defines a dataclass for sandbox execution results and an abstract interface for sandbox runners.
- **Depends on**: none
- **Structure**:
class SandboxResult
  def ok(self) -> bool:
  def format_for_llm(self) -> str:
class Sandbox
  def run(self, code: str, timeout: float = 10.0) -> SandboxResult:

#### `core/sandbox/docker.py`
- **Role**: infrastructure
- **Purpose**: Provides a Docker-based sandbox implementation that initializes with a project root and Docker image, but currently raises NotImplementedError for all operations.
- **Depends on**: core.sandbox.base
- **Structure**:
class DockerSandbox
  def __init__(self, project_root: Path, image: str):
  def run(self, code: str, timeout: float = 10.0) -> SandboxResult:

#### `core/sandbox/macos.py`
- **Role**: domain logic
- **Purpose**: Defines macOS sandbox execution for Python and TypeScript snippets, handling environment setup, command construction, and result truncation.
- **Depends on**: core.sandbox.base, sandbox-exec
- **Structure**:
class BaseMacOSSandbox
  def __init__(self, project_root: Path, profile_path: Path | None = None, max_output_bytes: int = 10_000):
  def file_extension(self) -> str:
  def _get_executable_args(self) -> List[str]:
  def _get_env(self, scratch_dir: Path) -> Dict[str, str]:
  def run(self, code: str, timeout: float = 10.0) -> SandboxResult:
  def _truncate(self, text: str) -> str:
class PythonMacOSSandbox
  def __init__(self, project_root: Path, python_executable: Path | None = None, **kwargs ):
  def _get_executable_args(self) -> List[str]:
  def _get_env(self, scratch_dir: Path) -> Dict[str, str]:
class NodeMacOSSandbox
  def __init__(self, project_root: Path, executable: str | Path = "node", is_typescript: bool = True, **kwargs):
  def file_extension(self) -> str:
  def _get_executable_args(self) -> List[str]:
  def _get_env(self, scratch_dir: Path) -> Dict[str, str]:

#### `core/web_search/base.py`
- **Role**: domain logic
- **Purpose**: Define the interface for asynchronous web search operations.
- **Depends on**: none
- **Structure**:
class SearchManager
  async def web_search(self, query: str, num_results: int, max_characters: int ) -> list[str]:

#### `core/web_search/exa.py`
- **Role**: domain logic
- **Purpose**: Provides asynchronous web search functionality using the Exa API and returns result snippets.
- **Depends on**: exa_py, core.web_search.base
- **Structure**:
class ExaSearch
  def __post_init__(self):
  async def web_search(self, query: str, num_results: int, max_characters: int ) -> list[str]:

#### `core/web_search/noop.py`
- **Role**: glue- **Purpose**: Provide a no-op implementation of SearchManager that logs a warning and raises NotImplementedError.
- **Depends on**: core.web_search.base, lib.logger
- **Structure**:
class NoopSearch
  async def web_search(self, query: str, num_results: int, max_characters: int ) -> list[str]:

#### `core/workflows/ask_llm.py`
- **Role**: domain logic
- **Purpose**: Resolves the agent container, constructs system and user messages, invokes the balanced LLM, extracts the response, and validates it before returning.
- **Depends on**: langchain_core.messages, core.container, core.exceptions, lib.logger, lib.helpers
- **Structure**:
async def main(question: str, container: AgentContainer | None = None) -> str:

#### `core/workflows/browse.py`
- **Role**: entry point
- **Purpose**: Orchestrates the browsing workflow by initializing Playwright tools, building a state graph, and executing the browsing loop.
- **Depends on**: langchain_core, langchain_mcp_adapters, langgraph, core.container, core.exceptions, lib.logger, lib.helpers
- **Structure**:
class BrowseState
def build_graph(container: AgentContainer, playwright_tools: list[BaseTool], num_rounds: int) -> StateGraph:
async def main(instruction: str, headless: bool = False, container: AgentContainer | None = None) -> str:

#### `core/workflows/build_context.py`
- **Role**: domain logic
- **Purpose**: Orchestrates the context‑building workflow, defining state, tool handling, and graph execution for context generation.
- **Depends on**: langchain_core.messages, langgraph.graph, core.container, core.exceptions, core.agent_tools, core.config, core.schemas, core.workflows.create_file_index, core.workflows.shared, lib.logger
- **Structure**:
def _handle_included_files(current: set[str], delta: dict[str, bool]) -> set[str]:
class AgentState
def build_graph(container) -> StateGraph:
async def main(instructions: str, container: AgentContainer | None = None ) -> list[ContextItem]:

#### `core/workflows/create_epic.py`
- **Role**: domain logic
- **Purpose**: Orchestrates creation of an epic plan by invoking LLMs, reviewing output, and persisting the final plan to a file.
- **Depends on**: langchain_core.messages, core.container, core.exceptions, lib.logger, lib.helpers
- **Structure**:
async def main(instructions: str, container: AgentContainer | None = None) -> str:

#### `core/workflows/create_file_index.py`
- **Role**: entry point
- **Purpose**: Creates a consolidated file index by summarizing each project file via LLM and writing the results to a markdown overview file.
- **Depends on**: langchain_core, tenacity, core.container, core.config, lib.helpers, lib.logger, lib.tree_parser, lib.treesitter_extractor
- **Structure**:
async def _invoke_llm(llm, messages):
async def process_file(file_path: str, container: AgentContainer, semaphore: asyncio.Semaphore ) -> str | None:
async def main(container: AgentContainer | None = None) -> str:

#### `core/workflows/create_overview.py`
- **Role**: glue
- **Purpose**: Merge file index into an overview summary and write it to the overview file.
- **Depends on**: core.container, core.exceptions, lib.helpers, lib.logger, lib.tree_parser, core.workflows.create_file_index, MCP client, LLM
- **Structure**:
async def main(container: AgentContainer | None = None) -> str:

#### `core/workflows/implement_task.py`
- **Role**: domain logic
- **Purpose**: Orchestrates a multi‑round LLM‑driven workflow that builds, executes, and refines code change proposals using tool calls.
- **Depends on**: langchain_core.messages, langchain_core.tools, core.agent_tools, core.container, core.exceptions, core.schemas, lib.logger
- **Structure**:
def _extract_verification_notes(history: list[BaseMessage], max_output_chars: int = 800 ) -> str:
async def _run_tool_loop(llm_with_tools: Llm, tools: list[BaseTool], initial_messages: list[BaseMessage] ) -> list[BaseMessage]:
async def main(prompt: str, container: AgentContainer | None = None ) -> CodeChangeResponse:

#### `core/workflows/plan_task.py`
- **Role**: domain logic
- **Purpose**: Orchestrates a multi‑round LLM planning workflow that resolves clarifications, reads files, and produces a final plan.
- **Depends on**: langchain_core.messages, langchain_core.tools, core.container, core.exceptions, core.agent_tools, core.schemas, lib.helpers, lib.logger
- **Structure**:
def _render_clarifications(args: dict) -> str:
def _render_read_files(files: dict[str, str]) -> str:
async def _run_tool_loop(llm: Llm, llm_with_tools: Llm, tools: list[BaseTool], initial_messages: list[BaseMessage]) -> tuple[AIMessage, list[BaseMessage]]:
async def main(prompt: str, container: AgentContainer | None = None) -> PlanResponse:

#### `core/workflows/research.py`
- **Role**: domain logic
- **Purpose**: Orchestrates multi‑round research workflow, managing state, tool invocation, and final synthesis to answer a user question.
- **Depends on**: langchain_core.messages, langgraph.graph, langgraph.graph.message, core.config, core.container, core.exceptions, core.agent_tools, core.workflows.summarize_item, lib.logger, lib.helpers, core.workflows.create_file_index
- **Structure**:
class ResearchState
def build_graph(container: AgentContainer, num_rounds: int) -> StateGraph:
async def main(question: str, container: AgentContainer | None = None) -> str:

#### `core/workflows/shared.py`
- **Role**: utility
- **Purpose**: Index project files by parsing the directory tree, filtering by language, and invoking the indexer.
- **Depends on**: core.container, core.config, search.indexer, lib.tree_parser, lib.treesitter_extractor, lib.logger
- **Structure**:
async def index_project(container: AgentContainer | None = None) -> dict:

#### `core/workflows/summarize_item.py`
- **Role**: glue
- **Purpose**: Summarize the provided content according to given instructions using the container's LLM.
- **Depends on**: core.container, core.exceptions, lib.logger, lib.helpers, langchain_core.messages, external LLM
- **Structure**:
async def main(content: str, instructions: str, container: AgentContainer | None = None ) -> str:

#### `core/agent_tools.py`
- **Role**: glue
- **Purpose**: Defines and assembles the set of agent tools that expose filesystem, search, and skill functionalities to the planning system. Provides helper functions for sandbox management and tool construction.
- **Depends on**: core.mcp_clients.filesystem.mcp_client_base, core.exceptions, core.sandbox, core.web_search.base, core.config, search.document_search, search.search, lib.logger
- **Structure**:
def get_sandbox(language: str) -> Sandbox:
class ToolName
def _is_file_not_found(exc: Exception) -> bool:
def skills_dir() -> Path:
async def list_skills_tool() -> list[str]:
async def get_skill_content_tool(filename: str) -> str:
def build_tools(mcp_client: FilesystemMcpClient, search_manager: SearchManager, allowed_tools: list[ToolName] | None = None) -> list[BaseTool]:

#### `core/config.py`
- **Role**: config
- **Purpose**: Loads and validates application settings from environment files, providing a singleton configuration object.
- **Depends on**: pydantic.error_wrappers, pydantic_settings, lib.logger
- **Structure**:
class LlmModel
class LlmModels
  def __post_init__(self):
class Settings
  def all_providers(self) -> list[Provider]:
  def validation_errors(self) -> str | None:
def _ensure_file(target: Path, example: Path) -> bool:
def get_env_file_path(project_path: Path) -> Path:
def init_settings():
def reload_settings() -> "Settings":
class _SettingsProxy
  def __getattr__(self, name):

#### `core/container.py`
- **Role**: glue
- **Purpose**: Create and manage Llm instances while coordinating core components such as MCP client, web search, and prompt configuration.
- **Depends on**: langchain_openai, langchain_core, langchain_google_genai, openai, pydantic, core.config, core.entities, core.prompt_config, core.schemas, core.mcp_clients.filesystem.mcp_client_base, core.mcp_clients.filesystem.local_filesystem_client, core.web_search.base, core.web_search.exa, core.web_search.noop, core.db, lib.logger, lib.helpers
- **Structure**:
class ReasoningStreamMixin
  def _convert_chunk_to_generation_chunk(self, chunk, default_chunk_class, base_generation_info ):
class ReasoningChatOpenAI
class KimiChatOpenAI
  def _create_chat_result(self, response: ChatCompletion | dict, generation_info: dict | None = None ) -> ChatResult:
  def _get_request_payload(self, input_: LanguageModelInput, *, stop: list[str] | None = None, **kwargs ) -> dict:
class Llm
  def bind_tools(self, tools, **kwargs) -> "Llm":
  async def ainvoke(self, messages: LanguageModelInput, **kwargs) -> AIMessage:
  async def ainvoke_structured(self, schema: type[T], messages: LanguageModelInput, **kwargs ) -> T:
  def _struct_kwargs(self, kwargs: dict) -> dict:
  def _post_to_stream(self, kind: StreamKind, data: str = "", can_stop: bool = True):
  def _extra_body(self) -> dict:
  def is_openai(self) -> bool:
  def is_deepseek(self) -> bool:
  def _extract_deltas(chunk) -> list[tuple[StreamKind, str]]:
class AgentContainer
  def __post_init__(self) -> None:
  def set_web_search(self) -> None:
  def set_model_mode(self, mode: Literal["standard", "high"]) -> None:
  def set_stream_listener(self, stream_listener: Callable[[StreamEvent], None]):
  def invalidate_llm_cache(self):
  def create_llm(self, provider: str, model: str, temperature: float, reasoning: bool, **kwargs ) -> Llm:
  async def get_ignore_list(self) -> list[str]:
  def do_cancel(self) -> bool:
  def summarization_model(self) -> tuple[str, str]:
  def strict_model(self) -> tuple[str, str]:
  def creative_model(self) -> tuple[str, str]:
  def llm_summarization(self) -> Llm:
  def llm_strict(self) -> Llm:
  def llm_coding(self) -> Llm:
  def llm_balanced(self) -> Llm:
  def llm_creative(self) -> Llm:
def get_container() -> AgentContainer:
def override_container(container: AgentContainer) -> None:
def reset_container() -> None:

#### `core/db.py`
- **Role**: infrastructure
- **Purpose**: Manages persistent storage of file overviews via SQLite. Provides async get/set operations and cache existence checks.
- **Depends on**: core.config.settings
- **Structure**:
class OverviewCache
  def __init__(self, db_path: Path = OVERVIEW_CACHE_DB_PATH):
  def _init_db(self):
  async def get_cached_overview(self, file_path: str, file_hash: str | None = None ) -> str | None:
  def _get_cached_overview(self, file_path: str, file_hash: str | None = None ) -> str | None:
  async def set_cached_overview(self, file_path: str, file_hash: str, summary: str):
  def _set_cached_overview(self, file_path: str, file_hash: str, summary: str):
  def is_empty(self) -> bool:

#### `core/entities.py`
- **Role**: domain logic
- **Purpose**: Track cumulative costs and provide methods to add costs and reset the total
- **Depends on**: none
- **Structure**:
class CostTracker
  def add_cost(self, amount: float) -> None:
  def reset(self):

#### `core/exceptions.py`
- **Role**: types/schema
- **Purpose**: Define custom exception hierarchy for the MCP agent.
- **Depends on**: none
- **Structure**:
class AgentError
class MCPConnectionError
class MCPToolError
  def __init__(self, tool_name: str, message: str) -> None:
class AgentInvocationError

#### `core/mcp_server.py`
- **Role**: entry point
- **Purpose**: Registers MCP server, defines available tools, and manages runtime state.
- **Depends on**: mcp.server, mcp.server.sse, mcp.types, lib.logger, search.document_search, search.search, core.config, core.container, core.workflows.build_context, core.workflows.shared, core.schemas
- **Structure**:
def register_state(state_info: Callable[[], StateInfo]):
async def list_tools():
async def call_tool(name: str, arguments: dict):

#### `core/prompt_config.py`
- **Role**: config
- **Purpose**: Loads and manages prompt templates from markdown files and provides a configurable collection of system prompts. Provides default prompt values through a singleton configuration object.
- **Depends on**: core.agent_tools, core.config
- **Structure**:
def get_prompt(name: str) -> str:
def get_build_context_prompt() -> str:
class PromptConfig
  def __init__(self, epic_plan_system_prompt: str | None = None, epic_plan_review_prompt: str | None = None, planning_system_prompt: str | None = None, planning_review_prompt: str | None = None, implementation_investigate_prompt: str | None = None, implementation_draft_prompt: str | None = None, implementation_review_prompt: str | None = None, file_overview_prompt: str | None = None, merge_overview_prompt: str | None = None, summarization_system_prompt: str | None = None, index_search_prompt: str | None = None, build_context_prompt: str | None = None, ask_llm_system_prompt: str | None = None, research_system_prompt: str | None = None, browse_system_prompt: str | None = None, user_prefix: str = "[Coding Agent — user request]") -> None:

#### `core/router.py`
- **Role**: glue- **Purpose**: Provides async wrapper functions that expose core workflows and container utilities to the application.
- **Depends on**: core.workflows.build_context, core.workflows.plan_task, core.workflows.implement_task, core.workflows.create_overview, core.workflows.create_epic, core.workflows.summarize_item, core.workflows.ask_llm, core.workflows.research, core.workflows.browse, core.container, core.schemas, core.agent_tools, core.config, search.document_indexer, search.document_search, search.db.database
- **Structure**:
async def build_context(instructions: str, container: AgentContainer | None = None ) -> list[ContextItem]:
async def plan_task(prompt: str, container: AgentContainer | None = None ) -> PlanResponse:
async def implement_task(prompt: str, container: AgentContainer | None = None ) -> CodeChangeResponse:
async def create_epic(instructions: str, container: AgentContainer | None = None ) -> str:
async def create_overview(container: AgentContainer | None = None) -> str:
async def summarize_context_item(content: str, instructions: str, container: AgentContainer | None = None ) -> str:
async def ask_llm(question: str, container: AgentContainer | None = None) -> str:
async def research(question: str, container: AgentContainer | None = None) -> str:
async def browse(instruction: str, headless: bool = False, container: AgentContainer | None = None ) -> str:
async def perform_web_search(query: str, container: AgentContainer | None = None ) -> str:
async def get_file_text(path: str, container: AgentContainer | None = None):
async def get_ignore_list(container: AgentContainer | None = None):
async def create_file(path: str, content: str, container: AgentContainer | None = None):
async def replace_text_in_file(path: str, old_text: str, new_text: str, container: AgentContainer | None = None ):
async def list_directory_tree(container: AgentContainer | None = None):
async def is_index_empty(container: AgentContainer | None = None):
async def run_ingestion(container: AgentContainer | None = None) -> str:
async def search_documents(query: str, k: int = 4, container: AgentContainer | None = None ) -> list[SearchResult]:
async def set_model_mode(mode: str, container: AgentContainer | None = None):
async def list_skills():
async def get_skill_content(filename: str):
async def get_total_cost(container: AgentContainer | None = None) -> float:
async def reset_cost(container: AgentContainer | None = None) -> float:
async def get_model_mode(container: AgentContainer | None = None) -> str:
async def cancel_llm_execution(container: AgentContainer | None = None):
async def config_validation_errors(_: AgentContainer | None = None) -> str | None:
async def get_settings_text(container: AgentContainer | None = None) -> str:
async def save_settings_text(content: str, container: AgentContainer | None = None ) -> None:

#### `core/schemas.py`
- **Role**: types/schema
- **Purpose**: Define data models and enums for plan responses, code changes, context items, and streaming events.
- **Depends on**: pydantic
- **Structure**:
class PlanResponse
class ContentType
class ContextItem
class CodeChange
class CodeChangeResponse
class StateInfo
class SearchResult
class StreamKind
class StreamEvent

#### `infra/alembic.ini`
- **Role**: config
- **Purpose**: Configure Alembic migration environment and database connection settings.
- **Depends on**: none

#### `infra/docker-compose.yml`
- **Role**: infrastructure
- **Purpose**: Defines the container orchestration for the agent database service and its persistent storage.
- **Depends on**: none

#### `infra/Dockerfile`
- **Role**: infrastructure
- **Purpose**: Builds a container image that runs PostgreSQL with ParadeDB extensions and preconfigured environment variables.
- **Depends on**: paradedb/paradedb

#### `infra/init.sql`
- **Role**: infrastructure
- **Purpose**: Ensure required PostgreSQL extensions are installed.
- **Depends on**: PostgreSQL

#### `lib/code_parser.py`
- **Role**: domain logic
- **Purpose**: Parse code_change blocks from input text and generate a summary with parsed changes.
- **Depends on**: core.schemas, lib.logger
- **Structure**:
def parse_code_changes(text: str, tag_name: str = TAG_NAME) -> CodeChangeResponse:

#### `lib/helpers.py`
- **Role**: utility
- **Purpose**: Compute token count, extract text and file contents from message histories, and provide an async context manager for duration logging.
- **Depends on**: tiktoken, langchain_core.messages, lib.logger
- **Structure**:
def context_size(context: str) -> int:
def extract_text_response(messages: list[BaseMessage]) -> str:
def extract_read_files(messages: list[BaseMessage]) -> dict[str, str]:
async def log_duration(extra: dict | None = None):

#### `lib/logger.py`
- **Role**: utility
- **Purpose**: Configure root logger and expose a get_logger function.
- **Depends on**: none
- **Structure**:
def _configure_root() -> None:
def get_logger(name: str) -> logging.Logger:

#### `lib/tree_parser.py`
- **Role**: utility
- **Purpose**: Parse hierarchical tree text into structured node objects, extract file paths, and render the tree as formatted text. Filter excluded directories and support navigable representations.
- **Depends on**: none
- **Structure**:
def parse_tree_to_nodes(tree_text: str, excluded: list[str] = None) -> list[dict]:
def all_tree_files(tree_nodes: list[dict]) -> list[str]:
def format_tree_as_text(tree_nodes: list[dict]) -> str:

#### `lib/treesitter_extractor.py`
- **Role**: utility
- **Purpose**: Extracts function, class, method, interface, and type signatures from source code and optionally chunks the file into logical components.
- **Depends on**: tree_sitter, tree_sitter_python, tree_sitter_javascript, tree_sitter_typescript, tree_sitter_go, lib.logger
- **Structure**:
def _get_signature_line(node: Node, code_bytes: bytes) -> str:
def _get_name(node: Node, code_bytes: bytes) -> str:
def _walk(node: Node, code_bytes: bytes, ext: str, depth: int = 0) -> list[str]:
def extract_signatures_from_content(file_path: str, content: str) -> str:
def chunk_file_content(file_path: str, content: str) -> list[dict]:

#### `search/chroma_poc/storage/indexer.py`
- **Role**: domain logic
- **Purpose**: Indexes a list of document chunks into a Chroma vector store using a SQL record manager and logs the result.
- **Depends on**: Chroma, SQLRecordManager, index, get_logger, search.config
- **Structure**:
def index_documents(chunks: list[Document], vector_store: Chroma) -> dict[str, Any]:

#### `search/chroma_poc/storage/retriever.py`
- **Role**: infrastructure
- **Purpose**: Searches a vector store for documents matching a query and returns ranked results.
- **Depends on**: lib.logger, search.chroma_poc.storage.vector_store, search.entities
- **Structure**:
def search_documents(query: str, k: int = 4) -> list[SearchResult]:

#### `search/chroma_poc/storage/vector_store.py`
- **Role**: infrastructure
- **Purpose**: Creates and caches a persistent Chroma vector store using HuggingFace embeddings.
- **Depends on**: langchain_huggingface, langchain_chroma, lib.logger, search.config
- **Structure**:
def get_vector_store() -> Chroma:

#### `search/chroma_poc/ingest.py`
- **Role**: domain logic
- **Purpose**: Orchestrates the local RAG ingestion pipeline, coordinating directory setup, file discovery, document loading, chunking, vector store indexing, and reporting.
- **Depends on**: lib.logger, search.config, search.entities, search.document_processing.discovery, search.document_processing.loaders, search.document_processing.splitters, search.chroma_poc.storage.vector_store, search.chroma_poc.storage.indexer
- **Structure**:
def setup_directories() -> None:
def run() -> IngestionSummary:

#### `search/db/migrations/versions/f10d916833f7_initial.py`
- **Role**: infrastructure
- **Purpose**: Create tables and indexes for code chunks, document chunks, and indexing metadata.
- **Depends on**: alembic.op, pgvector.sqlalchemy, sqlalchemy
- **Structure**:
def upgrade() -> None:
def downgrade() -> None:

#### `search/db/migrations/env.py`
- **Role**: glue
- **Purpose**: Configure Alembic migration environment and execute offline/online migrations based on settings.
- **Depends on**: sqlalchemy, alembic, core.config, search.db.models, PostgreSQL
- **Structure**:
def include_object(object, name, type_, reflected, compare_to):
def include_name(name, type_, parent_names):
def run_migrations_offline() -> None:
def run_migrations_online() -> None:

#### `search/db/migrations/README`
- **Role**: config
- **Purpose**: Defines the generic configuration for a single-database setup.
- **Depends on**: none

#### `search/db/migrations/script.py.mako`
- **Role**: infrastructure
- **Purpose**: Manage database schema migrations using Alembic revision scripts.
- **Depends on**: alembic, sqlalchemy

#### `search/db/database.py`
- **Role**: infrastructure
- **Purpose**: Creates and manages the database engine, session factory, and ensures schema migrations are applied.
- **Depends on**: sqlalchemy, alembic, core.config
- **Structure**:
def get_engine():
def get_session_local():
def new_session():
def get_db():
def ensure_schema_migrated():

#### `search/db/models.py`
- **Role**: types/schema
- **Purpose**: Define the database schema for code and document chunks, including embedding vectors and search indexes.
- **Depends on**: sqlalchemy, pgvector, search.ml_models
- **Structure**:
class Base
class CodeChunk
class IndexedFile
class DocumentChunk
class IndexedDocument

#### `search/db/repository.py`
- **Role**: infrastructure
- **Purpose**: Manages persistence and search operations for code and document chunks through repository classes.
- **Depends on**: pgvector.sqlalchemy, sqlalchemy, sqlalchemy.dialects.postgresql, sqlalchemy.orm, search.db.models, search.ml_models, paradedb
- **Structure**:
class CodeChunkRepository
  def __init__(self, session: Session):
  def delete_by_parent_file(self, parent_file: str) -> int:
  def insert_chunks(self, chunks: Iterable[CodeChunk]) -> int:
  def get_indexed_hash(self, parent_file: str) -> str | None:
  def upsert_indexed_file(self, parent_file: str, content_hash: str) -> None:
  def delete_indexed_file(self, parent_file: str) -> int:
  def list_indexed_files(self) -> list[str]:
  def hybrid_search(self, query_text: str, query_embedding: list[float], fetch_n: int = 10, candidate_pool: int = 100, rrf_k: int = 60) -> list[dict]:
class DocumentChunkRepository
  def __init__(self, session: Session):
  def delete_by_parent_file(self, parent_file: str) -> int:
  def insert_chunks(self, chunks: Iterable[DocumentChunk]) -> int:
  def get_indexed_hash(self, parent_file: str) -> str | None:
  def upsert_indexed_document(self, parent_file: str, content_hash: str) -> None:
  def delete_indexed_document(self, parent_file: str) -> int:
  def list_indexed_documents(self) -> list[str]:
  def hybrid_search(self, query_text: str, query_embedding: list[float], fetch_n: int = 10, candidate_pool: int = 100, rrf_k: int = 60) -> list[dict]:

#### `search/document_processing/discovery.py`
- **Role**: domain logic
- **Purpose**: Iterate over files in a base directory, yielding DiscoveredFile objects for supported extensions.
- **Depends on**: lib.logger, search.entities
- **Structure**:
def find_files(base_dir: Path) -> Iterator[DiscoveredFile]:

#### `search/document_processing/loaders.py`
- **Role**: domain logic
- **Purpose**: Load documents from discovered files using appropriate loaders and collect any loading errors.
- **Depends on**: lib.logger, langchain_core.documents, langchain_community.document_loaders.PyPDFLoader, langchain_community.document_loaders.TextLoader, langchain_community.document_loaders.UnstructuredMarkdownLoader, langchain_community.document_loaders.Docx2txtLoader, search.entities.DiscoveredFile
- **Structure**:
def load_documents(discovered_files: Iterable[DiscoveredFile]) -> tuple[list[Document], list[str]]:

#### `search/document_processing/splitters.py`
- **Role**: utility
- **Purpose**: Split documents into chunks using configured chunk size and overlap, adding chunk indices to metadata.
- **Depends on**: langchain_text_splitters, search.config
- **Structure**:
def split_documents(documents: Iterable[Document]) -> list[Document]:

#### `search/config.py`
- **Role**: config
- **Purpose**: Load configuration settings for search and define environment-specific constants.
- **Depends on**: core.config

#### `search/document_indexer.py`
- **Role**: domain logic
- **Purpose**: Indexes documents, splits them into chunks, generates embeddings, and updates the repository while tracking ingestion statistics.
- **Depends on**: search.ml_models, search.db.database, search.db.models, search.document_processing.splitters, search.document_processing.loaders, search.document_processing.discovery, search.db.repository, search.entities, lib.logger
- **Structure**:
class DocumentIndexStats
  def get_report(self) -> str:
def _normalize_rel(p: str) -> str:
class _IndexResult
def _index_document_file(rel_path: str, base_dir: str, repo: DocumentChunkRepository ) -> _IndexResult:
def index_document_files(paths: list[str], base_dir: str, delete_orphans: bool = True ) -> DocumentIndexStats:
def ingest_document_directory(target_path: str) -> DocumentIndexStats:

#### `search/document_search.py`
- **Role**: domain logic
- **Purpose**: Hybrid document search retrieves candidates via BM25 and vector ANN, then reranks with a cross‑encoder and returns top results.
- **Depends on**: search.db.database, search.db.repository, search.ml_models, lib.logger
- **Structure**:
def hybrid_document_search(query: str, fetch_n: int = 20, top_n: int = 4) -> list[dict]:

#### `search/entities.py`
- **Role**: types/schema
- **Purpose**: Defines data structures for discovered files, ingestion tracking, and search results.
- **Depends on**: none
- **Structure**:
class DiscoveredFile
class IngestionSummary
  def get_report(self) -> str:
class SearchResult

#### `search/indexer.py`
- **Role**: domain logic
- **Purpose**: Indexes source files into a searchable database, handling chunking, embedding, and orphan management.
- **Depends on**: search.ml_models.get_code_embedder, search.db.database.new_session, search.db.models.CodeChunk, search.db.repository.CodeChunkRepository, lib.logger.get_logger, lib.treesitter_extractor
- **Structure**:
class IndexStats
def _normalize_rel(p: str) -> str:
def index_files(paths: list[str], base_dir: str, delete_orphans: bool = True ) -> IndexStats:
def ingest_directory(target_path: str) -> IndexStats:
class _IndexResult
def _index_file(rel_path: str, base_dir: str, repo: CodeChunkRepository ) -> _IndexResult:
def _build_chunk_models(file_path: str, chunks: list[dict], signatures: str, embeddings: list[list[float]]) -> list[CodeChunk]:

#### `search/ml_models.py`
- **Role**: domain logic
- **Purpose**: Defines embedder and reranker implementations for code and document search, including model loading, embedding, and scoring logic.
- **Depends on**: mxbai_rerank, sentence_transformers, torch, search.config, lib.logger
- **Structure**:
class Embedder
  def dim(self) -> int:
  def embed_queries(self, texts: list[str]) -> list[list[float]]:
  def embed_documents(self, texts: list[str]) -> list[list[float]]:
class Reranker
  def score(self, query: str, documents: list[str]) -> list[float]:
class JinaCodeEmbedder
  def __init__(self) -> None:
  def dim(self) -> int:
  def _encode(self, texts: list[str]) -> list[list[float]]:
  def embed_queries(self, texts: list[str]) -> list[list[float]]:
  def embed_documents(self, texts: list[str]) -> list[list[float]]:
class NomicV15Embedder
  def __init__(self) -> None:
  def dim(self) -> int:
  def _encode(self, texts: list[str]) -> list[list[float]]:
  def embed_queries(self, texts: list[str]) -> list[list[float]]:
  def embed_documents(self, texts: list[str]) -> list[list[float]]:
class JinaRerankerV2
  def __init__(self) -> None:
  def score(self, query: str, documents: list[str]) -> list[float]:
class MxbaiRerankerV2
  def __init__(self) -> None:
  def score(self, query: str, documents: list[str]) -> list[float]: # mxbai.rank() returns results sorted by relevance — remap to input order. # Pass top_k explicitly: default behavior varies by mxbai-rerank version # and a silent top_k truncation would leave un-scored docs with sentinel # values, corrupting the final ranking.
def get_code_embedder() -> Embedder:
def get_doc_embedder() -> Embedder:
def get_reranker() -> Reranker:
def release_embedder_cache() -> None:
def warmup_code() -> None:
def warmup_documents() -> None:
def warmup() -> None:

#### `search/search.py`
- **Role**: domain logic
- **Purpose**: Implements hybrid search with two-stage retrieval, combining BM25 and vector ANN then reranking to return top results.
- **Depends on**: search.db.database, search.db.repository, search.ml_models, lib.logger
- **Structure**:
def hybrid_search(query: str, fetch_n: int = 10, top_n: int = 3) -> list[dict]:

#### `example.env`
- **Role**: config
- **Purpose**: Loads environment variables that configure the application's database, AI model providers, and other runtime settings.
- **Depends on**: PostgreSQL, NVIDIA API, Google API, OpenRouter, Kimi, Mimo, Alibaba

#### `example.ignore`
- **Role**: config
- **Purpose**: Excludes specified patterns from the agent's traversal.
- **Depends on**: none

#### `LICENSE`
- **Role**: config
- **Purpose**: Define the licensing terms governing distribution and modification of the software under the GNU Affero General Public License.
- **Depends on**: none

#### `pyproject.toml`
- **Role**: config
- **Purpose**: Defines project metadata, dependencies, and build configuration.
- **Depends on**: hatchling

#### `README.MD`
- **Role**: glue
- **Purpose**: Provide project overview and setup instructions for the Nice Coding Agent.
- **Depends on**: uv