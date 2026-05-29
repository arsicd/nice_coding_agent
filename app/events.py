import asyncio
import inspect
from enum import Enum
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from core.schemas import CodeChangeResponse
from lib.logger import get_logger

logger = get_logger(__name__)

Handler = Callable[..., Any]


@dataclass(frozen=True)
class LoadingChangedPayload:
    key: str
    loading: bool


@dataclass(frozen=True)
class LLMStateChangedPayload:
    status: str  # "idle" | "thinking" | "error"
    response: str = ""


@dataclass(frozen=True)
class ContextChangedPayload:
    pass


@dataclass(frozen=True)
class CostChangedPayload:
    cost: float


@dataclass(frozen=True)
class TreeLoadedPayload:
    pass


P = TypeVar("P")


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def on(self, event: str, handler: Handler) -> None:
        self._handlers[event].append(handler)

    def off(self, event: str, handler: Handler) -> None:
        try:
            self._handlers[event].remove(handler)
        except ValueError:
            pass

    def emit(self, event: str, payload: Any = None) -> None:
        for handler in self._handlers.get(event, []):
            if inspect.iscoroutinefunction(handler):
                logger.warning(
                    "EventBus.emit: skipping async handler %r for event %r — "
                    "use emit_async() to invoke async subscribers.",
                    handler.__name__,
                    event,
                )
                continue
            try:
                handler(payload)
            except Exception:
                logger.exception(
                    "EventBus.emit: handler %r raised for event %r", handler, event
                )

    async def emit_async(self, event: str, payload: Any = None) -> None:
        tasks = []
        for handler in self._handlers.get(event, []):
            try:
                result = handler(payload)
                if asyncio.iscoroutine(result):
                    tasks.append(result)
            except Exception:
                logger.exception(
                    "EventBus.emit_async: sync handler %r raised for event %r",
                    handler,
                    event,
                )
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    logger.exception(
                        "EventBus.emit_async: async handler raised for event %r: %r",
                        event,
                        r,
                    )

    def clear(self, event: str | None = None) -> None:
        if event is None:
            self._handlers.clear()
        else:
            self._handlers.pop(event, None)


@dataclass
class ImplementationPayload:
    status: str = "idle"  # "thinking" | "ready" | "error"
    response: CodeChangeResponse | None = None
    error: str | None = None


class Events(str, Enum):
    INSTRUCTIONS_CHANGED = "instructions_changed"
    CONTEXT_CHANGED = "context_changed"
    COST_CHANGED = "cost_changed"
    TREE_LOADED = "tree_loaded"
    LOADING_CHANGED = "loading_changed"
    IMPLEMENTATION_RESPONSE = "implementation_response"
    MODEL_MODE_SYNC = "model_mode_sync"
    STREAM_START = "stream_start"
    STREAM_CHUNK = "stream_chunk"
    STREAM_END = "stream_end"
