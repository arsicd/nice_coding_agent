# Project Architecture Overview

## 1. Project Summary

An AI-powered coding assistant that helps developers plan, implement, and review code changes through an interactive web UI. The system combines LLM-driven workflows with codebase understanding—indexing source files, managing context windows, and orchestrating multi-step agent operations. Built with Python, FastAPI, NiceGUI, and LangGraph, it supports multiple model providers and can operate against local filesystems or JetBrains IDEs via MCP.

## 2. Architecture

The system follows a layered architecture with clear separation between presentation, application, domain, and infrastructure concerns. The **presentation layer** (`app/`) renders a NiceGUI-based IDE interface and translates user interactions into application commands. The **application layer** (`app/controller.py`, `app/presenter.py`) coordinates UI state, event propagation, and delegates to domain workflows. The **domain layer** (`core/workflows/`, `core/agent_tools.py`) implements LLM-driven workflows as stateful graphs that plan, research, implement, and summarize code changes. The **infrastructure layer** (`core/mcp_clients/`, `core/sandbox/`, `search/`, `core/db.py`) provides filesystem abstraction, code execution sandboxes, vector search, and caching.

Data flows from user input through the UI → presenter → controller → workflow engine, which may invoke tools (filesystem, search, sandbox, web search), stream partial results back via events, and ultimately produce structured outputs (plans, code changes, summaries) that update the UI state.

## 3. Subsystem Map

| Module | Responsibility | Anchor Entry Points |
|--------|---------------|---------------------|
| **UI Components** (`app/components/`) | Renders dialogs, context stacks, stream views, and sidebar navigation for the IDE interface | `app/components/prompt_dock.py`, `app/components/context_stack.py`, `app/components/stream_view.py` |
| **Application Shell** (`app/`) | Manages global state, event bus, and coordinates between UI and domain workflows | `app/state.py`, `app/events.py`, `app/presenter.py`, `app/controller.py` |
| **Workflow Engine** (`core/workflows/`) | Orchestrates multi-step LLM workflows: planning, implementation, research, context building, and overview generation | `core/workflows/plan_task.py`, `core/workflows/implement_task.py`, `core/workflows/build_context.py`, `core/workflows/research.py` |
| **Agent Tools** (`core/agent_tools.py`) | Exposes filesystem, search, sandbox, and skill tools to workflows as LangChain-compatible tool interfaces | `core/agent_tools.py` |
| **LLM Infrastructure** (`core/container.py`, `core/config.py`) | Configures and creates LLM instances with provider-specific streaming, reasoning, and structured output support | `core/container.py`, `core/config.py` |
| **Filesystem Abstraction** (`core/mcp_clients/`) | Provides read/write/list operations against local filesystem or remote JetBrains IDE via MCP protocol | `core/mcp_clients/filesystem/local_filesystem_client.py`, `core/mcp_clients/filesystem/mcp_client_jetbrains.py` |
| **Code Execution Sandbox** (`core/sandbox/`) | Safely executes Python/Node.js code snippets with OS-specific isolation (macOS seatbelt, Linux bubblewrap) | `core/sandbox/base.py`, `core/sandbox/macos.py`, `core/sandbox/linux.py` |
| **Codebase Search** (`search/`) | Indexes source code and documents into vector stores with hybrid search (BM25 + embeddings + reranking) | `search/indexer.py`, `search/search.py`, `search/document_indexer.py`, `search/document_search.py` |
| **Search Storage** (`search/db/`, `search/chroma_poc/`) | Persists chunks and embeddings in PostgreSQL/pgvector or Chroma, with Alembic migrations | `search/db/models.py`, `search/db/repository.py`, `search/chroma_poc/storage/vector_store.py` |
| **Document Processing** (`search/document_processing/`) | Discovers, loads, and chunks documents for ingestion into search indexes | `search/document_processing/discovery.py`, `search/document_processing/loaders.py`, `search/document_processing/splitters.py` |
| **ML Models** (`search/ml_models.py`) | Manages embedding and reranking model lifecycle for code and document retrieval | `search/ml_models.py` |
| **Utilities** (`lib/`) | Shared parsing, token counting, tree parsing, Tree-sitter extraction, and logging | `lib/treesitter_extractor.py`, `lib/tree_parser.py`, `lib/helpers.py`, `lib/code_parser.py` |

## 4. Key Concepts

- **Context Stack** — Ordered collection of user-selected files, snippets, and generated artifacts fed into LLM prompts
- **Workflow** — Stateful, multi-turn LLM interaction graph (planning, implementation, research) with tool use loops
- **AgentContainer** — Dependency injection container holding configured LLM instances, MCP clients, and search backends
- **MCP Client** — Abstraction over filesystem operations, enabling local or IDE-remote file access via Model Control Protocol
- **Hybrid Search** — Two-stage retrieval combining sparse (BM25) and dense (vector ANN) methods with cross-encoder reranking
- **Sandbox** — Isolated code execution environment with OS-specific security profiles
- **Stream Event** — Typed, incremental LLM output (content, reasoning, tool calls) pushed to UI via event bus
- **Model Mode** — Quality/cost tier selection (standard vs. high) affecting which LLM provider and parameters are used

## 5. Architectural Constraints & Integrations

- **Multiple LLM Providers**: Supports OpenAI, Google GenAI, DeepSeek, Kimi, and others via LangChain adapters; configuration is provider-model-temperature-reasoning matrix
- **MCP Protocol**: Optional JetBrains IDE integration via MCP server; falls back to direct filesystem access
- **Vector Search Backends**: Dual support for PostgreSQL/pgvector (production) and Chroma (PoC/local), selected via configuration
- **Embedding Models**: Jina and Nomic embedders for code/documents; Jina and MXBAI rerankers for result ranking
- **Sandbox Security**: Platform-specific isolation required—macOS `sandbox-exec` with seatbelt profiles, Linux `bubblewrap`, Docker placeholder
- **Web Search**: Optional Exa API integration; degrades to no-op if unconfigured
- **Persistence**: SQLite for file overview caching; PostgreSQL for chunk/embedding storage with Alembic migrations
- **Deployment**: FastAPI server with NiceGUI; Docker Compose for PostgreSQL/ParadeDB; single-tenant desktop or server deployment