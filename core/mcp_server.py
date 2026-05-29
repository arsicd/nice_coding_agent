import asyncio
from typing import Callable

from mcp.server import Server
from mcp.server.sse import SseServerTransport
import mcp.types as types

from core.config import settings
from core.container import get_container
from core.workflows.build_context import main as main_build_context
from core.workflows.shared import index_project
from core.schemas import StateInfo
from lib.logger import get_logger
from search.document_search import hybrid_document_search
from search.search import hybrid_search

logger = get_logger(__name__)

mcp_server = Server("nicegui-tools")
sse_transport = SseServerTransport("/mcp/messages")

_state_info: Callable[[], StateInfo] | None = None


def register_state(state_info: Callable[[], StateInfo]):
    global _state_info
    _state_info = state_info


@mcp_server.list_tools()
async def list_tools():
    tools = [
        types.Tool(
            name="build_comprehensive_context",
            description=(
                "Triggers a background research agent that produces an implementation-ready "
                "markdown brief for a feature or bug. The brief includes full contents of "
                "relevant files (not snippets), project conventions, and likely gotchas.\n\n"
                "Use BEFORE writing code when the change spans multiple files, touches "
                "unfamiliar parts of the codebase, or would otherwise require 3+ `search_code` "
                "calls to orient. Skip for trivial edits, isolated one-file changes, or when "
                "you already have sufficient context from the current conversation.\n\n"
                "Latency: 15s–60s. Output is token-heavy since full files are returned — "
                "prefer `search_code` for targeted lookups."
            ),
            inputSchema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "task_prompt": {
                        "type": "string",
                        "minLength": 20,
                        "description": (
                            "Self-contained description of the feature to build or bug to fix. "
                            "The agent does NOT see prior conversation, so include: user-facing "
                            "behavior or symptom, suspected components/areas involved, relevant "
                            "constraints (perf, compat, style), and any error messages or repro "
                            "steps for bugs. Aim for a paragraph, not a sentence."
                        ),
                    }
                },
                "required": ["task_prompt"],
            },
        ),
        types.Tool(
            name="search_code",
            description=(
                "Hybrid search (vector + lexical, with cross-encoder reranking) over the "
                "project's indexed source code. Returns ranked code chunks with file path "
                "and rerank score.\n\n"
                "Queries can mix natural-language intent with literal tokens — function "
                "names, error strings, API names — and the reranker will sort relevance. "
                'Examples: "where do we validate JWT tokens", "rate limiting middleware", '
                '"retry_with_backoff usage", "ConnectionResetError handling".'
            ),
            inputSchema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "query": {
                        "type": "string",
                        "minLength": 3,
                        "description": "Search query — natural language, literal tokens, or both.",
                    },
                },
                "required": ["query"],
            },
        ),
    ]

    if settings.use_rag:
        tools.append(
            types.Tool(
                name="search_documents",
                description=(
                    "Hybrid search (vector + lexical, with cross-encoder reranking) over "
                    "ingested user documents (PDF/MD/TXT/DOCX from the `documents/` folder). "
                    "Returns matching chunks with source filename and rerank score.\n\n"
                    "Use for questions answerable from the user's personal/reference "
                    "documents (specs, design docs, manuals, notes). Queries can mix "
                    "natural-language intent with literal terms from the documents."
                ),
                inputSchema={
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "query": {
                            "type": "string",
                            "minLength": 3,
                            "description": "Search query — natural language, literal terms, or both.",
                        },
                        "k": {
                            "type": "integer",
                            "description": "Number of chunks to return (default 4).",
                            "minimum": 1,
                            "maximum": 20,
                            "default": 4,
                        },
                    },
                    "required": ["query"],
                },
            ),
        )

    return tools


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict):
    logger.info(f"Running tool {name}")

    if name == "build_comprehensive_context":
        resolved = get_container()
        context = await main_build_context(arguments["task_prompt"], resolved)
        parts = []
        for entry in context:
            parts.append(f"### {entry.type.value} - {entry.title}\n\n{entry.content}")
        return [types.TextContent(type="text", text="\n\n".join(parts))]

    if name == "search_code":
        await index_project()
        query = arguments["query"]
        results = await asyncio.to_thread(hybrid_search, query, 25, 8)
        if not results:
            return [types.TextContent(type="text", text="No matching code found.")]
        parts = [
            f"### {r['parent_file']}  (score: {r['rerank_score']:.4f})\n\n{r['content']}"
            for r in results
        ]
        return [types.TextContent(type="text", text="\n\n---\n\n".join(parts))]

    if name == "search_documents":
        query = arguments["query"]
        k = int(arguments.get("k", 4))
        results = await asyncio.to_thread(hybrid_document_search, query, top_n=k)
        if not results:
            return [types.TextContent(type="text", text="No matching documents found.")]
        parts = [
            f"### {r['parent_file']}  (score: {r['rerank_score']:.4f})\n\n{r['content']}"
            for r in results
        ]
        return [types.TextContent(type="text", text="\n\n---\n\n".join(parts))]

    raise NotImplementedError()
