import asyncio
import os
from enum import StrEnum
from pathlib import Path

from langchain_core.tools import tool, BaseTool

from core.mcp_clients.filesystem.mcp_client_base import FilesystemMcpClient
from core.exceptions import MCPToolError
from core.sandbox import Sandbox, make_sandbox
from core.web_search.base import SearchManager
from core.config import settings
from search.document_search import hybrid_document_search
from search.search import hybrid_search
from lib.logger import get_logger

logger = get_logger(__name__)

TOOL_ERROR_PREFIX = "[Tool error]"

_sandbox_cache = {}


def get_sandbox(language: str) -> Sandbox:
    if language not in _sandbox_cache:
        _sandbox_cache[language] = make_sandbox(
            project_root=Path(settings.project_root), language=language
        )
    return _sandbox_cache[language]


class ToolName(StrEnum):
    LIST_DIRECTORY_TREE = "list_directory_tree"
    GET_FILE_TEXT = "get_file_text"
    INVESTIGATE_FILE = "investigate_file"
    WEB_SEARCH = "web_search"
    SEARCH_LOCAL_DOCUMENTS = "search_local_documents"
    SEARCH_CODE = "search_code"
    LIST_SKILLS = "list_skills"
    GET_SKILL_CONTENT = "get_skill_content"
    ASK_CLARIFICATION = "ask_clarification"
    INCLUDE_IN_CONTEXT = "include_in_context"
    EXCLUDE_FROM_CONTEXT = "exclude_from_context"
    RUN_SCRATCH_CODE = "run_scratch_code"


_FILE_NOT_FOUND_HINTS = ("not found", "no such file", "does not exist")


def _is_file_not_found(exc: Exception) -> bool:
    if isinstance(exc, FileNotFoundError):
        return True
    msg = str(exc).lower()
    return any(hint in msg for hint in _FILE_NOT_FOUND_HINTS)


def skills_dir() -> Path:
    return Path(str(settings.project_root)).resolve() / ".nice" / "skills"


async def list_skills_tool() -> list[str]:
    if not os.path.exists(skills_dir()):
        return []
    return [
        f
        for f in os.listdir(skills_dir())
        if os.path.isfile(os.path.join(skills_dir(), f))
    ]


async def get_skill_content_tool(filename: str) -> str:
    path = skills_dir() / filename
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_tools(
    mcp_client: FilesystemMcpClient,
    search_manager: SearchManager,
    allowed_tools: list[ToolName] | None = None,
) -> list[BaseTool]:

    def _format_error(tool_name: str, exc: Exception) -> str:
        if isinstance(exc, MCPToolError):
            return f"{TOOL_ERROR_PREFIX} {exc}"
        return f"{TOOL_ERROR_PREFIX} '{tool_name}' failed unexpectedly: {exc}"

    @tool
    async def list_directory_tree() -> str:
        """Returns the directory tree of the current project.
        Use this first to discover available files before calling get_file_text."""
        try:
            return await mcp_client.list_directory_tree()
        except Exception as exc:
            logger.warning("list_directory_tree failed: %s", exc)
            return _format_error("list_directory_tree", exc)

    @tool
    async def get_file_text(path: str) -> str:
        """Returns the full text content of a specific file in the project."""
        try:
            return await mcp_client.get_file_text(path)
        except Exception as exc:
            if _is_file_not_found(exc):
                logger.info("get_file_text: path not found '%s'", path)
                return f"File not found: '{path}'. "
            logger.warning("get_file_text failed for '%s': %s", path, exc)
            return _format_error("get_file_text", exc)

    @tool
    async def investigate_file(path: str) -> str:
        """Returns the full text content of a specific file for INVESTIGATION ONLY.

        Calling this tool does NOT add the file to the final context handed to
        the downstream planning stage. Use it to read a file so you can decide
        whether it's relevant. If you decide it is relevant, call
        `include_in_context` to actually add it to the final context.

        You do NOT need to call this before `include_in_context` — if you're
        already confident a file is needed, include it directly using `include_in_context`.
        """
        try:
            return await mcp_client.get_file_text(path)
        except Exception as exc:
            if _is_file_not_found(exc):
                logger.info("investigate_file: path not found '%s'", path)
                return f"File not found: '{path}'. "
            logger.warning("investigate_file failed for '%s': %s", path, exc)
            return _format_error("investigate_file", exc)

    @tool
    async def web_search(query: str) -> str:
        """Performs a web search to find documentation, solutions, or API references.
        Use this if the instruction requires external knowledge outside the project."""
        try:
            results = await search_manager.web_search(query, 2, 1000)
            return "\n".join(results)
        except Exception as exc:
            logger.warning("web_search failed for '%s': %s", query, exc)
            return _format_error("web_search", exc)

    @tool
    async def search_local_documents(query: str) -> str:
        """Searches the local RAG index for relevant documents, notes, or internal knowledge.
        Use this if the instruction may be answered by previously indexed project docs, PDFs, or markdown files.
        """
        try:
            results = await asyncio.to_thread(
                hybrid_document_search, query, fetch_n=20, top_n=4
            )
            if not results:
                return "(no local documents found)"
            lines = []
            for r in results:
                lines.append(f"Source: {r['parent_file']}")
                lines.append(f"Score: {r['rerank_score']:.4f}")
                lines.append(f"Content:\n{r['content']}")
                lines.append("-" * 40)
            return "\n".join(lines)
        except Exception as exc:
            logger.warning("search_local_documents failed for '%s': %s", query, exc)
            return _format_error("search_local_documents", exc)

    @tool
    async def search_code(query: str) -> str:
        """Hybrid search over the project's indexed code chunks (BM25 + vector
        + cross-encoder rerank). Returns the most relevant chunks of source code
        with their file path, type (function/class/method), and name.

        Prefer this over reading entire files when you need to locate specific
        logic, find usages of a concept, or pull in implementation details
        without knowing the exact file. Use natural-language queries describing
        what the code does, not just identifiers — e.g.
        "reciprocal rank fusion of BM25 and vector results" rather than just
        "RRF".
        """
        try:
            results = await asyncio.to_thread(hybrid_search, query, 25, 8)
            if not results:
                return "(no matching code chunks found)"
            blocks = []
            for r in results:
                header = (
                    f"{r['parent_file']}  ::  " f"{r['chunk_type']} {r['chunk_name']}"
                )
                blocks.append(f"--- {header} ---\n{r['content']}")
            return "\n\n".join(blocks)
        except Exception as exc:
            logger.warning("search_code failed for '%s': %s", query, exc)
            return _format_error("search_code", exc)

    @tool
    async def list_skills() -> list[str]:
        """
        Returns a list of all available skills in the system.
        Use this tool to discover what specialized capabilities, agent skills,
        or skill filenames exist before attempting to load their specific content.
        """
        return await list_skills_tool()

    @tool
    async def get_skill_content(filename: str) -> str:
        """
        Retrieves the detailed instructions, code, or knowledge contained within a specific skill.

        Args:
            filename (str): The exact name of the skill file to load.

        Use this tool when you need to know how to execute a particular skill or need
        to read its internal documentation to fulfill the user's request.
        """
        return await get_skill_content_tool(filename)

    @tool
    def ask_clarification(
        questions: list[str],
        options: list[list[str]],
        answer_template: str,
    ) -> str:
        """Ask the user clarifying questions before producing a plan.

        Call this tool ONLY when architectural ambiguity would fundamentally
        change the plan. Do not call it for minor details.

        Args:
            questions: The questions to ask, in order. Each item is a single concise question.
            options: For each question, a list of labeled options the user can choose from
                (e.g. ["A) psycopg v3", "B) psycopg2", "C) asyncpg"]). Mark the recommended
                default by appending " ✓" to that option. Must be the same length as questions.
            answer_template: A short template showing the user how to reply, with one numbered
                slot per question (e.g. "Q1: _\nQ2: _"). The user fills these in.
        """
        return "CLARIFICATION_REQUESTED"

    @tool
    def include_in_context(paths: list[str]) -> str:
        """Marks files for inclusion in the final context handed to the
        downstream planning stage.

        This is the ONLY way a project file reaches the planner. `get_file_text`
        and `search_code` are investigation tools — their output does not reach
        the planner. You do NOT need to have read a file with `get_file_text`
        before including it: if `search_code` hits, file index entries, or
        imports in other files make it clear a file is needed, include it
        directly. Conversely, files you read only to understand context but
        which the change will not touch should NOT be included.

        Accepts a list of paths so you can batch inclusions in a single call.

        Args:
            paths: Relative paths of files to include in the final context.
        """
        return "INCLUDE_REQUESTED"

    @tool
    def exclude_from_context(paths: list[str]) -> str:
        """Removes previously included files from the final context.

        Use this when later investigation reveals a file you included with
        `include_in_context` is not actually needed by the change. Excluding
        a path that was never included is a no-op.

        Args:
            paths: Relative paths of files to remove from the final context.
        """
        return "EXCLUDE_REQUESTED"

    @tool
    async def run_scratch_code(code: str, language: str) -> str:
        """
        Execute a code snippet to verify a specific factual assumption about
        code you are about to change. Useful when getting an API signature,
        return type, or data shape wrong would make your diff incorrect.

        Call this when you have a concrete, named uncertainty and the answer isn't
        visible in your context. A quick check here prevents a wrong diff.

        Skip it for trivial tasks, basic or standard lib behavior, or things
        you already know. This tool is for verification, not for applying or
        testing fixes.

        Sandbox: project importable, filesystem read-only, no network, 10s timeout.

        Args:
            code: Source code to execute.
            language: The language to run ("python", "node", "typescript").
        """
        sandbox = get_sandbox(language)
        result = await asyncio.to_thread(sandbox.run, code, 10.0)
        return result.format_for_llm()

    all_tools = [
        list_directory_tree,
        get_file_text,
        investigate_file,
        web_search,
        search_local_documents,
        search_code,
        list_skills,
        get_skill_content,
        ask_clarification,
        include_in_context,
        exclude_from_context,
        run_scratch_code,
    ]

    if allowed_tools is not None:
        allowed_tool_names = {tool_name.value for tool_name in allowed_tools}
        return [t for t in all_tools if t.name in allowed_tool_names]

    return all_tools
