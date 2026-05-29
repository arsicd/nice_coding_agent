from contextlib import asynccontextmanager
import time

import tiktoken

from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from lib.logger import get_logger

logger = get_logger(__name__)


def context_size(context: str) -> int:
    model = "cl100k_base"
    token_encoder = tiktoken.get_encoding(model)
    return len(token_encoder.encode(context))


def extract_text_response(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        content = message.content

        if isinstance(content, str):
            text = content.strip()
            if text:
                return text

        elif isinstance(content, list):
            text_parts = [
                block.get("text", "").strip()
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            combined = "\n".join(p for p in text_parts if p)
            if combined:
                return combined

    return ""


def extract_read_files(messages: list[BaseMessage]) -> dict[str, str]:
    """Walk the message history and return {path: content} for successful
    get_file_text calls. If the same file was read multiple times, last wins.
    """
    pending: dict[str, str] = {}
    files: dict[str, str] = {}

    for msg in messages:
        if isinstance(msg, AIMessage):
            for call in getattr(msg, "tool_calls", []) or []:
                if call["name"] == "get_file_text":
                    path = (call.get("args") or {}).get("path")
                    if path:
                        pending[call["id"]] = path
        elif isinstance(msg, ToolMessage):
            path = pending.pop(msg.tool_call_id, None)
            if path is None:
                continue
            content = str(msg.content)
            if content.startswith("[Tool error]") or content.startswith("Error:"):
                continue
            files[path] = content

    return files


@asynccontextmanager
async def log_duration(extra: dict | None = None):
    start = time.perf_counter()
    payload = {}
    try:
        yield payload
    finally:
        logger.debug(
            {"duration": round(time.perf_counter() - start, 1)}
            | payload
            | (extra or {})
        )
