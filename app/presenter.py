import asyncio
import contextlib
from dataclasses import dataclass
import os as _os
import uuid

from nicegui import ui

from core.schemas import CodeChange, SearchResult, ContentType
from app.controller import AppController
from app.events import Events, ImplementationPayload
from app.exceptions import AgentError, EmptyContextError, MCPError, FileReadError
from app.state import AppState
from lib.logger import get_logger

logger = get_logger(__name__)

EPIC_PLAN_FILE_NAME = ".nice/epic_plan.md"
PRD_FILE_NAME = ".nice/prd.md"
OVERVIEW_FILE_NAME = ".nice/project_overview.md"


@dataclass
class AppPresenter:
    _state: AppState
    _ctrl: AppController

    async def on_model_mode_change(self, mode: str) -> None:
        await self._ctrl.set_model_mode(mode)

    async def on_cancel_llm(self) -> None:
        await self._ctrl.cancel_llm_execution()

    async def get_skills(self) -> list[str]:
        return await self._ctrl.list_skills()

    async def get_settings_text(self) -> str:
        return await self._ctrl.get_settings_text()

    async def on_save_settings(self, content: str) -> None:
        try:
            await self._ctrl.save_settings_text(content)
            ui.notify("Settings saved", type="positive")
        except Exception as exc:
            ui.notify(f"Failed to save settings: {exc}", type="negative")

    async def on_add_skill(self, filename: str) -> None:
        try:
            entry_id = f"skill_{filename}"
            raw_content = await self._ctrl.get_skill_content(filename)
            rendered_md = f"**Skill: {filename}**\n\n```\n{raw_content}\n```"
            self._state.add_context_entry(
                entry_id=entry_id,
                label=f"🛠️ {filename}",
                content=rendered_md,
                raw_content=raw_content,
                is_loading=False,
                editable=False,
                is_minimized=True,
            )
            ui.notify(f"Skill '{filename}' added", type="positive")
        except Exception as exc:
            ui.notify(f"Failed to add skill: {exc}", type="negative")

    async def on_implement(self) -> None:
        self._state.bus.emit(
            Events.IMPLEMENTATION_RESPONSE, ImplementationPayload(status="thinking")
        )
        try:
            async with self._loading("implement"):
                result = await self._ctrl.implement_task()
            cost = await self._ctrl.get_total_cost()
            self._state.set_cost(cost)
            self._state.bus.emit(
                Events.IMPLEMENTATION_RESPONSE,
                ImplementationPayload(status="ready", response=result),
            )
            self._state.implementation = result
        except EmptyContextError as exc:
            ui.notify(str(exc), type="warning")
            self._state.bus.emit(
                Events.IMPLEMENTATION_RESPONSE,
                ImplementationPayload(status="error", error=str(exc)),
            )
        except AgentError as exc:
            self._state.bus.emit(
                Events.IMPLEMENTATION_RESPONSE,
                ImplementationPayload(status="error", error=f"⚠️ LLM Error: {exc}"),
            )
        except Exception as exc:
            logger.exception("Unexpected error in on_implement")
            self._state.bus.emit(
                Events.IMPLEMENTATION_RESPONSE,
                ImplementationPayload(
                    status="error", error=f"⚠️ Unexpected Error: {exc}"
                ),
            )

    async def on_plan(self) -> None:
        entry_id = f"plan_{uuid.uuid4().hex[:8]}"
        self._state.add_context_entry(
            entry_id=entry_id,
            label="📋 Plan",
            content="",
            is_loading=True,
            editable=True,
            render_as_markdown=True,
        )
        try:
            async with self._loading("plan_task"):
                result = await self._ctrl.plan_task()
            cost = await self._ctrl.get_total_cost()
            self._state.set_cost(cost)
            for file_path in result.loaded_files:
                await self.on_open_file_path(file_path)
            self._state.update_context_entry(
                entry_id=entry_id,
                content=result.summary,
                raw_content=result.summary,
                is_loading=False,
                render_as_markdown=True,
            )
        except EmptyContextError as exc:
            ui.notify(str(exc), type="warning")
            self._state.remove_context_entry(entry_id)
        except Exception as exc:
            logger.exception("Unexpected error in on_plan")
            self._state.update_context_entry(
                entry_id=entry_id,
                content=f"**Plan Error:** {exc}",
                is_loading=False,
            )

    async def on_apply_change(self, change: CodeChange) -> None:
        await self._ctrl.apply_code_change(change)
        ui.notify(
            f"✅ Applied to {change.file_path}",
            type="positive",
            timeout=3000,
        )

    def on_remove_implementation(self) -> None:
        self._state.bus.emit(
            Events.IMPLEMENTATION_RESPONSE, ImplementationPayload(status="idle")
        )

    async def on_summarize_entry(self, entry_id: str) -> None:
        try:
            summary = await self._ctrl.summarize_context_item(entry_id)
            rendered_content = f"**Summary:**\n\n{summary}"
            self._state.update_context_entry(
                entry_id=entry_id,
                content=rendered_content,
                raw_content=summary,
                is_loading=False,
            )
            logger.info(f"Summarization done")
            ui.notify(f"Summarization done")
        except Exception as exc:
            logger.info(f"Summarization failed: {exc}")
            ui.notify(f"Summarization failed", type="negative")

    def on_update_context_entry(self, entry_id: str, new_raw: str) -> None:
        entry = self._state.get_context_entry(entry_id)
        if entry and entry.render_as_markdown:
            self._state.update_context_entry(
                entry_id=entry_id,
                content=new_raw,
                raw_content=new_raw,
                render_as_markdown=True,
            )
            return
        self._state.update_context_entry(
            entry_id=entry_id, content=new_raw, raw_content=new_raw
        )

    async def on_copy_all(self) -> None:
        await self._ctrl.reload_context_files()
        text = self._state.build_llm_prompt()
        if not text:
            ui.notify("Context is empty.", type="warning")
            return
        escaped = text.replace("`", "\\`").replace("${", "\\${")
        await ui.run_javascript(f"""
            navigator.clipboard.writeText(`{escaped}`)
              .then(() => console.log('copied'))
              .catch(err => console.error('copy failed', err));
        """)
        ui.notify("Context copied to clipboard!", type="positive", timeout=2000)

    def on_clear_context(self) -> None:
        self._state.clear_context()
        self._state.bus.emit(
            Events.IMPLEMENTATION_RESPONSE,
            ImplementationPayload(status="idle"),
        )

    def on_remove_context_entry(self, entry_id: str) -> None:
        self._state.remove_context_entry(entry_id)

    def on_update_instructions(self, instructions: str) -> None:
        self._state.update_instructions(instructions)

    async def on_open_file_path(self, path: str) -> None:
        if not path:
            return
        if any(entry.id == path for entry in self._state.context_entries):
            self._state.remove_context_entry(path)
            return
        self._state.add_context_entry(
            entry_id=path,
            label=f"📄 {path}",
            content="",
            is_loading=True,
            editable=False,
            is_minimized=True,
        )
        await self._fetch_and_render(path)

    async def on_node_click(self, e) -> None:
        node_id: str = e.value
        if not node_id:
            return

        node = self._ctrl.get_tree_node(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")

        if not node["is_folder"]:
            await self.on_open_file_path(node_id)
        else:
            file_paths = self._ctrl.collect_files_under_folder(node_id)
            if not file_paths:
                ui.notify(f"No files found in: {node_id}", type="info")
                return
            for fp in file_paths:
                self._state.add_context_entry(
                    entry_id=fp,
                    label=f"📄 {fp}",
                    content="",
                    is_loading=True,
                    editable=False,
                    is_minimized=True,
                )
            await asyncio.gather(*[self._fetch_and_render(fp) for fp in file_paths])

    async def _fetch_and_render(
        self, file_path: str, is_minimized: bool = True
    ) -> None:
        try:
            entry = self._state.get_context_entry(file_path)
            if not entry:
                return

            raw_content = await self._ctrl.fetch_file_content(file_path)
            if entry.render_as_markdown:
                content = raw_content
            else:
                content = entry.file_content_md(raw_content)
            self._state.update_context_entry(
                entry_id=entry.id,
                content=content,
                raw_content=raw_content,
                is_loading=False,
                is_minimized=is_minimized,
            )
        except MCPError as exc_:
            self._state.update_context_entry(
                entry_id=file_path,
                content=f"> ⚠️ Failed to load: {exc_}",
                is_loading=False,
            )
        except Exception:
            self._state.update_context_entry(
                entry_id=file_path,
                content="> ⚠️ Unexpected error loading file",
                is_loading=False,
            )

    async def on_ask_llm(self, question: str) -> None:
        entry_id = f"ask_llm_{uuid.uuid4().hex[:8]}"
        self._state.add_context_entry(
            entry_id=entry_id,
            label="💬 Ask LLM",
            content="",
            is_loading=True,
            editable=False,
            render_as_markdown=True,
        )
        try:
            answer = await self._ctrl.ask_llm(question)
            content = f"**Question:** {question}\n\n**Answer:**\n{answer}"
            self._state.update_context_entry(
                entry_id=entry_id,
                content=content,
                raw_content=answer,
                is_loading=False,
            )
        except Exception as exc:
            self._state.update_context_entry(
                entry_id=entry_id,
                content=f"**Question:** {question}\n\n**Error:** {exc}",
                is_loading=False,
            )

    async def on_research(self, question: str) -> None:
        entry_id = f"research_{uuid.uuid4().hex[:8]}"
        self._state.add_context_entry(
            entry_id=entry_id,
            label="🔬 Research",
            content="",
            is_loading=True,
            editable=False,
            render_as_markdown=True,
        )
        try:
            answer = await self._ctrl.research(question)
            content = f"**Question:** {question}\n\n**Research Result:**\n{answer}"
            self._state.update_context_entry(
                entry_id=entry_id,
                content=content,
                raw_content=answer,
                is_loading=False,
            )
        except Exception as exc:
            self._state.update_context_entry(
                entry_id=entry_id,
                content=f"**Question:** {question}\n\n**Error:** {exc}",
                is_loading=False,
            )

    async def on_browse(self, instruction: str) -> None:
        entry_id = f"browse_{uuid.uuid4().hex[:8]}"
        self._state.add_context_entry(
            entry_id=entry_id,
            label="🔬 Browse Result",
            content="",
            is_loading=True,
            editable=False,
            render_as_markdown=True,
        )
        try:
            answer = await self._ctrl.browse(instruction)
            content = f"**Instruction:** {instruction}\n\n**Browse Result:**\n{answer}"
            self._state.update_context_entry(
                entry_id=entry_id,
                content=content,
                raw_content=answer,
                is_loading=False,
            )
        except Exception as exc:
            self._state.update_context_entry(
                entry_id=entry_id,
                content=f"**Instruction:** {instruction}\n\n**Error:** {exc}",
                is_loading=False,
            )

    async def on_web_search(self, query: str) -> None:
        entry_id = f"web_search_{uuid.uuid4().hex[:8]}"
        self._state.add_context_entry(
            entry_id=entry_id,
            content="",
            raw_content="",
            is_loading=True,
            label="📋 Web Search Results",
        )
        try:
            summary = await self._ctrl.web_search(query)
        except Exception as exc:
            self._state.remove_context_entry(entry_id)
            ui.notify(str(exc), type="warning")
            return
        rendered_md = f"**Web search summary:**\n\n{summary}"
        self._state.update_context_entry(
            entry_id=entry_id,
            content=rendered_md,
            raw_content=summary,
            is_loading=False,
        )

    async def on_documents_ingest(self) -> str:
        async with self._loading("documents_ingest"):
            try:
                return await self._ctrl.run_documents_ingestion()
            except Exception as exc:
                logger.exception("Documents ingestion failed")
                raise AgentError(f"Ingestion failed: {exc}")

    async def on_documents_search(self, query: str) -> list[SearchResult]:
        try:
            return await self._ctrl.search_documents(query)
        except Exception as exc:
            logger.exception("Documents search failed")
            raise AgentError(f"Search failed: {exc}")

    def on_add_document_to_context(self, result: SearchResult) -> None:
        entry_id = f"doc_{uuid.uuid4().hex[:8]}"
        rendered_md = (
            f"**Document: {result.source}** (score: {result.score:.4f})\n\n"
            f"```\n{result.content}\n```"
        )
        self._state.add_context_entry(
            entry_id=entry_id,
            label=f"📚 {result.source}",
            content=rendered_md,
            raw_content=result.content,
            editable=False,
            is_minimized=True,
        )
        ui.notify(f"Added '{result.source}' to context", type="positive")

    async def on_add_additional_context(self) -> None:
        entry_id = f"additional_{uuid.uuid4().hex[:8]}"
        self._state.add_context_entry(
            entry_id=entry_id,
            label="Additional Context",
            content="",
            raw_content="",
        )

    async def on_build_context(self) -> None:
        loading_id = f"context_loading_{uuid.uuid4().hex[:8]}"
        self._state.add_context_entry(
            entry_id=loading_id,
            content="",
            raw_content="",
            is_loading=True,
            label="📋 Building Context...",
        )

        try:
            async with self._loading("build_context"):
                items = await self._ctrl.build_context()
            cost = await self._ctrl.get_total_cost()
            self._state.set_cost(cost)
            self._state.remove_context_entry(loading_id)
            render_as_markdown = False
            for item in items:
                if item.type == ContentType.file:
                    file_path = item.title
                    entry_id = file_path
                    label = f"📄 {file_path}"
                    editable = False
                    file_ext = _os.path.splitext(file_path)[1].lstrip(".")
                    raw_content = item.content
                    content = f"```{file_ext}\n{raw_content}\n```"
                elif item.type == ContentType.skill:
                    filename = item.title
                    entry_id = f"skill_{filename}"
                    label = f"🛠️ {filename}"
                    editable = False
                    raw_content = item.content
                    content = f"**Skill: {filename}**\n\n```\n{raw_content}\n```"
                elif item.type == ContentType.project_overview:
                    entry_id = OVERVIEW_FILE_NAME
                    label = "🧭 Project Overview"
                    editable = False
                    content = raw_content = item.content
                    render_as_markdown = True
                else:
                    entry_id = f"ctx_{uuid.uuid4().hex[:8]}"
                    label = item.title
                    editable = True
                    content = raw_content = item.content
                self._state.add_context_entry(
                    entry_id=entry_id,
                    label=label,
                    content=content,
                    raw_content=raw_content,
                    editable=editable,
                    is_minimized=True,
                    render_as_markdown=render_as_markdown,
                )
        except EmptyContextError as exc:
            self._state.remove_context_entry(loading_id)
            ui.notify(str(exc), type="warning")
        except Exception as exc:
            self._state.remove_context_entry(loading_id)
            ui.notify(f"Build context failed: {exc}", type="warning")

    async def on_create_overview(self) -> None:
        async with self._loading("create_overview"):
            results = await self._ctrl.create_overview()
            ui.notify(results)
            cost = await self._ctrl.get_total_cost()
            self._state.set_cost(cost)

    async def on_create_epic(self) -> None:
        entry_id = EPIC_PLAN_FILE_NAME
        self._state.add_context_entry(
            entry_id=entry_id,
            label="🗺️ Epic Plan",
            content="",
            editable=False,
            is_loading=True,
            render_as_markdown=True,
        )
        try:
            await self._ctrl.reload_context_files()
            prompt = self._state.build_llm_prompt()
            if not prompt:
                raise EmptyContextError()
            await self._ctrl.create_epic(prompt)
            cost = await self._ctrl.get_total_cost()
            self._state.set_cost(cost)
            await self._fetch_and_render(entry_id, False)
        except EmptyContextError as exc:
            ui.notify(str(exc), type="warning")
            self._state.remove_context_entry(entry_id)
        except Exception as exc:
            logger.exception("Create epic failed")
            self._state.update_context_entry(
                entry_id=entry_id,
                content=f"**Epic Error:** {exc}",
                is_loading=False,
            )

    async def on_load_epic(self) -> None:
        entry_id = EPIC_PLAN_FILE_NAME
        self._state.add_context_entry(
            entry_id=entry_id,
            label=f"🗺️ Epic Plan",
            content="",
            is_loading=True,
            editable=False,
            is_minimized=True,
            render_as_markdown=True,
        )
        await self._fetch_and_render(entry_id, True)

    async def on_load_prd(self) -> None:
        entry_id = PRD_FILE_NAME
        self._state.add_context_entry(
            entry_id=entry_id,
            label=f"📄 {PRD_FILE_NAME}",
            content="",
            is_loading=True,
            editable=False,
            is_minimized=True,
            render_as_markdown=True,
        )
        await self._fetch_and_render(entry_id, True)

    async def on_load_overview(self) -> None:
        entry_id = OVERVIEW_FILE_NAME
        self._state.add_context_entry(
            entry_id=entry_id,
            label="🧭 Project Overview",
            content="",
            is_loading=True,
            editable=False,
            is_minimized=True,
            render_as_markdown=True,
        )
        await self._fetch_and_render(entry_id, True)

    async def on_load_tree(self) -> None:
        async with self._loading("tree"):
            try:
                await self._ctrl.load_file_tree()
            except Exception as exc:
                ui.notify(f"Tree error: {exc}", type="negative")

    async def load_agents_file(self) -> None:
        path = ".nice/AGENTS.md"
        try:
            content = await self._ctrl.fetch_file_content(path)
        except FileReadError:
            content = None
        if not content:
            return
        await self.on_open_file_path(path)
        entry = self._state.get_context_entry(path)
        entry.pinned = True

    async def check_first_run(self):
        is_empty = await self._ctrl.is_index_empty()
        if is_empty:
            with (
                ui.dialog() as warning_dialog,
                ui.card()
                .classes("dialog-card-themed flex flex-col")
                .style("width: 90vw; max-width: 560px;"),
            ):
                with ui.element("div").classes("dialog-head w-full"):
                    ui.html(
                        '<span class="dialog-title">'
                        '<span class="dialog-title-glyph">⚠️</span>First run'
                        "</span>"
                    )

                with ui.element("div").classes("dialog-body w-full"):
                    ui.html(
                        "<div style='font-weight:600; margin-bottom:0.6rem;'>Before you start, do the following:</div>"
                        "<ul style='list-style:none; margin:0; padding:0; line-height:1.6;'>"
                        "<li style='display:flex; gap:0.6rem; align-items:flex-start; margin-bottom:0.4rem;'>"
                        "<span style='opacity:0.7;'>☐</span>"
                        "<span>Adjust <code>.nice/.env</code> to configure database and llm providers.</span>"
                        "</li>"
                        "<li style='display:flex; gap:0.6rem; align-items:flex-start; margin-bottom:0.4rem;'>"
                        "<span style='opacity:0.7;'>☐</span>"
                        "<span>Adjust <code>.nice/.ignore</code> to exclude files you don't want to index.</span>"
                        "</li>"
                        "<li style='display:flex; gap:0.6rem; align-items:flex-start; margin-bottom:0.4rem;'>"
                        "<span style='opacity:0.7;'>☐</span>"
                        "<span>Check the file tree contains only files you want indexed — use the reload button after editing <code>.nice/.ignore</code>.</span>"
                        "</li>"
                        "<li style='display:flex; gap:0.6rem; align-items:flex-start;'>"
                        "<span style='opacity:0.7;'>☐</span>"
                        "<span>Run <strong>Create Overview</strong> before any other action to index the files.</span>"
                        "</li>"
                        "</ul>"
                    )

                with ui.element("div").classes("dialog-foot"):
                    ok_btn = ui.element("button").classes("cmdbtn primary")
                    with ok_btn:
                        ui.html("<span>OK</span>")
                    ok_btn.on("click", lambda _e: warning_dialog.close())
            warning_dialog.open()

    async def on_add_tree_to_context(self) -> None:
        async with self._loading("add_tree"):
            entry_id = "file_tree"
            self._state.add_context_entry(
                entry_id=entry_id,
                label="🌳 File Tree",
                content="",
                is_loading=True,
                editable=False,
                is_minimized=True,
            )
            try:
                if not self._state.tree_loaded:
                    await self._ctrl.load_file_tree()
                tree_text = self._ctrl.format_tree_as_text()
                rendered_md = f"**Project file tree:**\n\n```\n{tree_text}\n```"
                self._state.update_context_entry(
                    entry_id=entry_id,
                    content=rendered_md,
                    raw_content=tree_text,
                    is_loading=False,
                    is_minimized=True,
                )
            except Exception as exc:
                self._state.remove_context_entry(entry_id)
                ui.notify(f"Failed to load tree: {exc}", type="negative")

    @contextlib.asynccontextmanager
    async def _loading(self, key: str):
        self._state.set_loading(key, True)
        try:
            yield
        finally:
            self._state.set_loading(key, False)
