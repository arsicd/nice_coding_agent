import argparse
import uuid
from pathlib import Path

from nicegui import Client, app, ui
from fastapi import Request
from pydantic.error_wrappers import ValidationError

from core.config import settings
from core.mcp_server import mcp_server, sse_transport, register_state
from core.container import get_container
from app.controller import AppController
from app.events import Events
from app.presenter import AppPresenter
from app.router import Router
from app.state import AppState
from app.theme import apply_theme
from app.components.sidebar import SidebarView
from app.components.stack_header import StackHeaderView
from app.components.context_stack import ContextStackView
from app.components.context_actions import ContextActions
from app.components.prompt_dock import PromptDockView
from app.components.implementation_view import ImplementationView
from app.components.web_search_view import WebSearchView
from app.components.ask_llm_view import AskLlmView
from app.components.browse_view import BrowseView
from app.components.documents_view import DocumentsView
from app.components.settings_view import SettingsView
from app.components.skills_view import SkillsView
from app.components.stream_view import StreamView
from lib.logger import get_logger
from search.db.database import ensure_schema_migrated

logger = get_logger(__name__)

TITLE = "Context Builder"
STATIC_DIR = Path(__file__).parent / "static"
app.add_static_files("/static", str(STATIC_DIR))


@app.get("/mcp/sse")
async def sse_endpoint(request: Request):
    """Client connects here to establish the SSE stream."""
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_server.run(
            streams[0], streams[1], mcp_server.create_initialization_options()
        )


@app.post("/mcp/messages")
async def messages_endpoint(request: Request):
    """Client POSTs tool execution requests here."""
    await sse_transport.handle_post_message(
        request.scope, request.receive, request._send
    )


_owner: dict[str, str | None] = {"token": None}


async def acquire_slot(client: Client) -> bool:
    await client.connected()

    token = app.storage.tab.get("token")

    if _owner["token"] is None:
        token = token or str(uuid.uuid4())
        app.storage.tab["token"] = token
        _owner["token"] = token
        return True

    return token == _owner["token"]


def show_blocked() -> None:
    ui.label(
        "This app is already open in another tab. To use it here instead, close the other tab and restart the app."
    ).classes("text-2xl")


async def validate_config(
    controller: AppController, settings_view: SettingsView
) -> None:
    errors = await controller.config_validation_errors()
    if errors:
        ui.notify(errors, type="warning")
        await settings_view.open()
    else:
        ensure_schema_migrated()


@ui.page("/")
async def index(client: Client) -> None:
    if not await acquire_slot(client):
        show_blocked()
        return

    apply_theme()
    state = AppState()
    get_container().set_stream_listener(state.on_stream_event)
    register_state(state.state_info)
    controller = AppController(state=state, _router=Router())
    presenter = AppPresenter(state, controller)

    implementation_panel = ImplementationView(
        on_close=presenter.on_remove_implementation,
        on_apply=presenter.on_apply_change,
    )

    web_search_view = WebSearchView(presenter.on_web_search)
    ask_llm_view = AskLlmView(presenter.on_ask_llm, presenter.on_research)
    browse_view = BrowseView(presenter.on_browse)
    settings_view = SettingsView(
        presenter.get_settings_text, presenter.on_save_settings
    )
    skills_view = SkillsView(presenter.get_skills, presenter.on_add_skill)
    stream_view = StreamView(state, on_cancel=presenter.on_cancel_llm)

    documents_view = None
    if settings.use_rag:
        documents_view = DocumentsView(
            presenter.on_documents_ingest,
            presenter.on_documents_search,
            presenter.on_add_document_to_context,
        )

    with ui.element("div").classes("app"):
        sidebar = SidebarView(
            state,
            on_node_click=presenter.on_node_click,
            on_refresh=presenter.on_load_tree,
            on_create_overview=presenter.on_create_overview,
            on_add_tree=presenter.on_add_tree_to_context,
            on_load_overview=presenter.on_load_overview,
        )

        with ui.element("main").classes("stack has-dock"):
            stack_header = StackHeaderView(
                state, presenter.on_model_mode_change, settings_view.open
            )
            stream_view.render()

            with ui.element("div").classes("stack-body"):
                ctx_stack = ContextStackView(
                    state,
                    presenter.on_remove_context_entry,
                    presenter.on_update_context_entry,
                    presenter.on_summarize_entry,
                )
                ctx_stack.render()

                add_row = ContextActions(
                    on_add_additional=presenter.on_add_additional_context,
                    on_open_skills=skills_view.open,
                    on_open_ask=ask_llm_view.open,
                    on_open_browse=browse_view.open,
                    on_open_search=web_search_view.open,
                    on_open_docs=documents_view.open if documents_view else None,
                )
                add_row.render()

            dock = PromptDockView(
                state,
                presenter.on_update_instructions,
                presenter.on_build_context,
                presenter.on_create_epic,
                presenter.on_load_epic,
                presenter.on_load_prd,
                presenter.on_plan,
                presenter.on_implement,
                presenter.on_clear_context,
                presenter.on_copy_all,
            )

    state.bus.on(Events.CONTEXT_CHANGED, ctx_stack.refresh)
    state.bus.on(Events.CONTEXT_CHANGED, sidebar.on_context_changed)
    state.bus.on(Events.CONTEXT_CHANGED, stack_header.on_context_changed)
    state.bus.on(Events.COST_CHANGED, stack_header.on_cost_changed)
    state.bus.on(Events.MODEL_MODE_SYNC, stack_header.on_model_mode_sync)
    state.bus.on(Events.INSTRUCTIONS_CHANGED, stack_header.on_context_changed)
    state.bus.on(Events.TREE_LOADED, sidebar.refresh)
    state.bus.on(Events.LOADING_CHANGED, sidebar.on_loading_changed)
    state.bus.on(Events.LOADING_CHANGED, dock.on_loading_changed)
    state.bus.on(
        Events.IMPLEMENTATION_RESPONSE, implementation_panel.on_implementation_changed
    )
    state.bus.on(Events.STREAM_START, stream_view.on_stream_start)
    state.bus.on(Events.STREAM_CHUNK, stream_view.on_stream_chunk)
    state.bus.on(Events.STREAM_END, stream_view.on_stream_end)

    await client.connected()
    await presenter.on_load_tree()
    await presenter.load_agents_file()
    await presenter.check_first_run()
    await controller.reset_cost()
    await controller.sync_model_mode()

    await validate_config(controller, settings_view)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    try:
        ui.run(title=TITLE, host=args.host, port=args.port, reload=False, dark=False)
    except KeyboardInterrupt:
        pass


if __name__ in {"__main__", "__mp_main__"}:
    main()
