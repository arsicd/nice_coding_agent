# Project Architecture Overview

## Project Summary

**Nice Coding Agent** is an AI-powered development assistant that helps developers understand, plan, implement, research, and document code within their projects. It provides a conversational web UI for interacting with LLM agent workflows that can read/write the local filesystem, search code and documents, run sandboxed code, and browse the web. The system is built with Python using NiceGUI for the frontend, LangChain/LangGraph for LLM orchestration, and PostgreSQL (ParadeDB) with pgvector for hybrid search.

## Architecture

The system follows a layered MVC-inspired pattern for the UI, with a workflow engine at its core. The **presentation layer** (`app/`) uses a Presenter–Controller–State triad coordinated by an async event bus. The Presenter translates user interactions into Controller calls; the Controller delegates to the **core router**, which dispatches to **LangGraph-based agent workflows** (`core/workflows/`). Each workflow (plan, implement, research, browse, build-context, etc.) is a state-machine graph that orchestrates multi-round LLM interactions with tool calls against filesystem, search, and sandbox services.

Below the workflows sit two major subsystems: the **LLM container** (`core/container.py`) which manages model instances, provider abstraction, streaming, and cost tracking; and the **search subsystem** (`search/`) which provides hybrid code and document retrieval via BM25 + vector ANN + cross-encoder reranking, backed by PostgreSQL with pgvector. Filesystem access is abstracted behind an MCP client interface, supporting both direct local I/O and JetBrains IDE integration via the MCP protocol. A sandbox layer provides isolated code execution on macOS (and eventually Docker) for agent verification steps.

## Subsystem Map

| Module | Responsibility | Anchor Entry Points |
|--------|---------------|---------------------|
| **App UI Components** (`app/components/`) | Render all interactive views (prompt dock, context stack, sidebar, streaming console, dialogs) | `prompt_dock.py`, `stream_view.py`, `sidebar.py` |
| **App Presentation Logic** (`app/`) | Presenter translates UI events to controller actions; Controller orchestrates workflows; State manages context and emits events | `presenter.py`, `controller.py`, `state.py` |
| **App Events** (`app/events.py`) | Async event bus and typed payload definitions for decoupling UI from logic | `EventBus`, `Events` enum |
| **Core Agent Container** (`core/container.py`) | Factory and registry for LLM instances, model provider abstraction, streaming, cost tracking | `AgentContainer`, `get_container()` |
| **Core Workflows** (`core/workflows/`) | LangGraph state-machine workflows for each agent capability | `plan_task.py`, `implement_task.py`, `research.py`, `build_context.py`, `browse.py` |
| **Core Router** (`core/router.py`) | Thin async facade exposing all core capabilities (workflows, filesystem, search, config) | `core/router.py` module-level functions |
| **Core Agent Tools** (`core/agent_tools.py`) | Assembles tool definitions (filesystem, search, sandbox, skills) for LLM tool-calling | `build_tools()`, `ToolName` enum |
| **Core MCP Clients** (`core/mcp_clients/`) | Filesystem abstraction supporting local I/O and JetBrains IDE via MCP protocol | `mcp_client_base.py`, `local_filesystem_client.py`, `mcp_client_jetbrains.py` |
| **Core Config & Prompts** (`core/config.py`, `core/prompt_config.py`) | Settings from env, prompt template loading from markdown files | `Settings`, `PromptConfig` |
| **Search Engine** (`search/`) | Hybrid code/document indexing and retrieval with embeddings, BM25, and cross-encoder reranking | `indexer.py`, `search.py`, `document_indexer.py`, `document_search.py` |
| **Search Storage** (`search/db/`) | PostgreSQL schema, migrations, and repository layer for code/document chunks with pgvector | `models.py`, `repository.py`, `database.py` |
| **Sandbox** (`core/sandbox/`) | Isolated code execution (macOS sandbox-exec, Docker planned) for agent verification | `base.py`, `macos.py` |
| **Library** (`lib/`) | Shared utilities: tree-sitter code extraction, directory tree parsing, token counting, logging | `treesitter_extractor.py`, `tree_parser.py`, `helpers.py` |

## Key Concepts

- **ContextEntry** — A unit of user-assembled context (file, snippet, search result) displayed as a card and composed into the LLM prompt.
- **AgentContainer** — Central dependency holder for LLM instances, MCP client, web search, config, and cost tracker; created once and threaded through all workflows.
- **Workflow** — A LangGraph state machine that orchestrates a multi-round LLM conversation with tool calls to accomplish a high-level task (plan, implement, research, etc.).
- **Hybrid Search** — Two-stage retrieval combining BM25 full-text and pgvector ANN, followed by cross-encoder reranking, used for both code chunks and document chunks.
- **MCP Client** — Filesystem abstraction (read, write, list, replace) that supports both direct local access and remote IDE integration via the Model Control Protocol.
- **Sandbox** — Sandboxed execution environment (macOS sandbox-exec profiles) for running agent-generated code safely during verification.
- **Event Bus** — Async pub/sub system decoupling UI views from application state changes (loading, context, cost, stream events).
- **PromptTemplate** — Markdown-based system prompt loaded from `core/prompts/` and customizable via `PromptConfig`.
- **Model Mode** — Toggle between "standard" and "high" model tiers, switching the underlying LLM provider/model for cost-versus-quality control.
- **StreamEvent** — Typed streaming token/reasoning chunks pushed from the LLM container through the event bus to the streaming console UI.
- **CostTracker** — Per-session accumulator of LLM API costs, displayed in the UI and resettable by the user.

## Architectural Constraints & Integrations

- **LLM Providers**: Pluggable via LangChain — supports OpenAI-compatible, Google Gemini, DeepSeek, Kimi, and OpenRouter endpoints; configured through environment variables.
- **Database**: PostgreSQL with ParadeDB extensions and pgvector for hybrid search; schema managed by Alembic migrations. Also uses a local SQLite file for file-overview caching.
- **Filesystem Access**: Abstracted behind MCP protocol — supports local filesystem (with gitignore-aware filtering) and JetBrains IDE integration over SSE.
- **UI Framework**: NiceGUI (built on FastAPI + Vue/Quasar) for the single-page web interface; SSE transport for MCP server communication.
- **Embedding/Reranking Models**: Local models via sentence-transformers (Jina Code, Nomic) for embeddings; mxbai-rerank / Jina for cross-encoder reranking.
- **Web Search**: Exa API integration for external web research; pluggable via `SearchManager` interface.
- **Code Parsing**: Tree-sitter for Python, JavaScript, TypeScript, and Go signature extraction and chunking.
- **Sandbox Isolation**: macOS sandbox-exec with read-only profiles; Docker backend defined but not yet implemented.
- **Deployment**: Docker Compose for PostgreSQL; application runs as a local process via `uv`/`hatch`.
- **Key Invariants**: The event bus is the sole mechanism for UI↔logic communication; all LLM calls flow through `AgentContainer` for consistent model selection, streaming, and cost tracking; filesystem mutations are always proxied through MCP clients, never done directly.