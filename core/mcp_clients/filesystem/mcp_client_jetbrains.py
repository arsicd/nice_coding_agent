import asyncio
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.sse import sse_client

from core.mcp_clients.filesystem.mcp_client_base import FilesystemMcpClient
from lib.logger import get_logger
from core.config import settings
from core.exceptions import MCPConnectionError, MCPToolError

logger = get_logger(__name__)

_PROJECT_ROOT = str(settings.project_root)


_MAX_RETRIES = 3
_BASE_BACKOFF = 1.0
_MAX_BACKOFF = 16.0


class _SessionManager:
    def __init__(self) -> None:
        self._session: ClientSession | None = None
        self._exit_stack: AsyncExitStack | None = None
        self._lock = asyncio.Lock()

    async def get_session(self) -> ClientSession:
        async with self._lock:
            if self._session is not None:
                return self._session
            return await self._connect()

    async def _connect(self) -> ClientSession:
        last_exc: Exception | None = None
        backoff = _BASE_BACKOFF

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                stack = AsyncExitStack()
                streams = await stack.enter_async_context(
                    sse_client(url=settings.jetbrains_mcp_url)
                )
                session = await stack.enter_async_context(ClientSession(*streams))
                await session.initialize()

                self._session = session
                self._exit_stack = stack
                logger.info("MCP session established", extra={"attempt": attempt})
                return session

            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "MCP connect attempt %d/%d failed: %s",
                    attempt,
                    _MAX_RETRIES,
                    exc,
                )
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(min(backoff, _MAX_BACKOFF))
                    backoff *= 2

        raise MCPConnectionError(
            f"Could not connect to JetBrains MCP at {settings.jetbrains_mcp_url} "
            f"after {_MAX_RETRIES} attempts"
        ) from last_exc

    async def reconnect(self) -> ClientSession:
        async with self._lock:
            await self._close_unsafe()
            return await self._connect()

    async def close(self) -> None:
        async with self._lock:
            await self._close_unsafe()

    async def _close_unsafe(self) -> None:
        if self._exit_stack:
            try:
                await self._exit_stack.aclose()
            except Exception:
                logger.debug("Error while closing MCP exit stack", exc_info=True)
            finally:
                self._exit_stack = None
                self._session = None
                logger.info("MCP session closed")


_manager = _SessionManager()


async def get_session() -> ClientSession:
    return await _manager.get_session()


async def close_session() -> None:
    await _manager.close()


async def _call_tool(tool_name: str, arguments: dict) -> str:
    result = None
    for is_retry in (False, True):
        try:
            session = await _manager.get_session()
            result = await session.call_tool(tool_name, arguments=arguments)
            break
        except MCPConnectionError:
            raise
        except Exception as exc:
            if is_retry:
                raise MCPConnectionError(
                    f"MCP tool call '{tool_name}' failed after reconnect"
                ) from exc
            logger.warning(
                "MCP call '%s' failed (%s), attempting reconnect…", tool_name, exc
            )
            await _manager.reconnect()
    assert result

    errors = [
        b.text for b in result.content if hasattr(b, "type") and b.type == "error"
    ]
    if errors:
        raise MCPToolError(tool_name, "; ".join(errors))

    texts = [b.text for b in result.content if hasattr(b, "text")]
    return "\n".join(texts) if texts else "(empty response)"


class McpClientJetbrains(FilesystemMcpClient):
    async def get_file_text(self, path: str) -> str:
        return await _call_tool(
            "get_file_text_by_path",
            arguments={"pathInProject": path, "projectPath": _PROJECT_ROOT},
        )

    async def list_directory_tree(self) -> str:
        return await _call_tool(
            "list_directory_tree",
            arguments={"directoryPath": _PROJECT_ROOT, "projectPath": _PROJECT_ROOT},
        )

    async def replace_text_in_file(
        self, path: str, old_text: str, new_text: str
    ) -> str:
        return await _call_tool(
            "replace_text_in_file",
            arguments={
                "pathInProject": path,
                "oldText": old_text,
                "newText": new_text,
                "projectPath": _PROJECT_ROOT,
                "replaceAll": False,
            },
        )

    async def create_file(self, path: str, content: str) -> str:
        return await _call_tool(
            "create_new_file",
            arguments={
                "pathInProject": path,
                "text": content,
                "projectPath": _PROJECT_ROOT,
                "overwrite": True,
            },
        )
