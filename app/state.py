from dataclasses import dataclass, field
from typing import Literal

import tiktoken

from app.events import (
    EventBus,
    Events,
    ContextChangedPayload,
    LoadingChangedPayload,
    TreeLoadedPayload,
    CostChangedPayload,
)
from app.models.context_entry import ContextEntry
from core.schemas import StateInfo, CodeChangeResponse, StreamEvent, StreamKind
from lib.helpers import context_size

LLMStatus = Literal["idle", "thinking", "error"]


@dataclass
class AppState:
    bus: EventBus = field(default_factory=EventBus)
    model: str = "cl100k_base"
    context_entries: list[ContextEntry] = field(default_factory=list)
    instructions: str = ""
    implementation: CodeChangeResponse | None = None
    total_cost: float = 0.0
    llm_status: LLMStatus = "idle"
    stream_text: str = ""
    stream_reasoning: str = ""
    _tree_nodes: list[dict] = field(default_factory=list)
    _tree_loaded: bool = False
    _loading: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self._token_encoder = tiktoken.get_encoding(self.model)

    def update_instructions(self, instructions: str) -> None:
        self.instructions = instructions
        self.bus.emit(Events.INSTRUCTIONS_CHANGED)

    def set_model_mode(self, mode: str) -> None:
        self.bus.emit(Events.MODEL_MODE_SYNC, mode)

    def set_loading(self, key: str, value: bool) -> None:
        if value:
            self._loading.add(key)
        else:
            self._loading.discard(key)
        self.bus.emit(
            Events.LOADING_CHANGED, LoadingChangedPayload(key=key, loading=value)
        )

    def set_cost(self, cost: float) -> None:
        self.total_cost = cost
        self.bus.emit(Events.COST_CHANGED, CostChangedPayload(cost=cost))

    def is_loading(self, key: str) -> bool:
        return key in self._loading

    @property
    def tree_nodes(self) -> list[dict]:
        return self._tree_nodes

    @tree_nodes.setter
    def tree_nodes(self, value: list[dict]) -> None:
        self._tree_nodes = value

    @property
    def tree_loaded(self) -> bool:
        return self._tree_loaded

    @tree_loaded.setter
    def tree_loaded(self, value: bool) -> None:
        self._tree_loaded = value
        if value:
            self.bus.emit(Events.TREE_LOADED, TreeLoadedPayload())

    def get_context_entry(self, entry_id: str) -> ContextEntry | None:
        for existing in self.context_entries:
            if existing.id == entry_id:
                return existing
        return None

    def add_context_entry(
        self,
        entry_id: str,
        label: str,
        content: str = "",
        raw_content: str = "",
        is_loading: bool = False,
        editable: bool = True,
        is_minimized: bool = False,
        pinned: bool = False,
        render_as_markdown: bool = False,
    ) -> ContextEntry:
        existing = self.get_context_entry(entry_id)
        if existing:
            return existing

        new_entry = ContextEntry(
            id=entry_id,
            label=label,
            content=content,
            raw_content=raw_content,
            is_loading=is_loading,
            editable=editable,
            is_minimized=is_minimized,
            pinned=pinned,
            render_as_markdown=render_as_markdown,
        )
        self.context_entries.append(new_entry)
        self.bus.emit(Events.CONTEXT_CHANGED, ContextChangedPayload())
        return new_entry

    def update_context_entry(
        self,
        entry_id: str,
        content: str,
        raw_content: str = "",
        is_loading: bool = False,
        is_minimized: bool = False,
        render_as_markdown: bool | None = None,
    ) -> None:
        entry = self.get_context_entry(entry_id)
        if not entry:
            return

        entry.content = content
        entry.raw_content = raw_content
        entry.is_loading = is_loading
        entry.is_minimized = is_minimized
        if render_as_markdown is not None:
            entry.render_as_markdown = render_as_markdown

        self.bus.emit(Events.CONTEXT_CHANGED, ContextChangedPayload())

    def get_context(self) -> list[str]:
        parts = []
        for entry in self.context_entries:
            if not entry.is_loading:
                text = entry.raw_content if entry.raw_content else entry.content
                parts.append(f"# {entry.label}\n\n{text}")
        return parts

    def build_llm_prompt(self) -> str:
        parts = self.get_context()
        parts.append(f"# USER INSTRUCTIONS\n\n{self.instructions}")
        return "\n\n".join(parts)

    def state_info(self) -> StateInfo:
        return StateInfo(
            context="\n\n".join(self.get_context()),
            instructions=self.instructions,
            implementation=self.implementation,
        )

    def remove_context_entry(self, entry_id: str) -> None:
        self.context_entries = [e for e in self.context_entries if e.id != entry_id]
        self.bus.emit(Events.CONTEXT_CHANGED, ContextChangedPayload())

    def clear_context(self) -> None:
        self.context_entries = [e for e in self.context_entries if e.pinned]
        self.bus.emit(Events.CONTEXT_CHANGED, ContextChangedPayload())

    def context_size(self) -> int:
        combined = "\n".join(e.content or "" for e in self.context_entries)
        combined += "\n" + self.instructions
        return context_size(combined)

    def on_stream_event(self, event: StreamEvent) -> None:
        if event.kind == StreamKind.START:
            self.bus.emit(Events.STREAM_START, event)
        elif event.kind == StreamKind.REASONING:
            self.stream_reasoning += event.delta
            self.bus.emit(Events.STREAM_CHUNK, event)
        elif event.kind == StreamKind.TEXT:
            self.stream_text += event.delta
            self.bus.emit(Events.STREAM_CHUNK, event)
        elif event.kind == StreamKind.END:
            self.bus.emit(Events.STREAM_END, event)
        else:
            raise NotImplementedError(f"Event kind not supported: {event.kind}")

    def clear_stream(self) -> None:
        self.stream_text = ""
        self.stream_reasoning = ""
