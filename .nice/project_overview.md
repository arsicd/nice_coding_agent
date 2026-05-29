# Project Architecture Overview

## 1. Project Summary

This is an AI-powered coding assistant that operates as both an interactive desktop application and an MCP (Model Context Protocol) server. It orchestrates LLM-driven workflows—planning, implementation, research, and code analysis—while managing a rich context system of files, documents, and conversation history. The system is built in Python using NiceGUI for the interface, LangChain/LangGraph for agent orchestration, and integrates multiple model providers through a unified abstraction layer.

## 2. Architecture

The system follows a layered architecture with three primary tiers: **Presentation**, **Application Core**, and **Infrastructure**. The Presentation layer (NiceGUI-based UI) renders a dark IDE-like interface with context stacks, file trees, and prompt docks, communicating via an event bus. The Application Core contains workflow orchestration (LangGraph state machines), agent tooling, and a dependency container that manages LLM instances and service lifecycles. The Infrastructure layer provides filesystem access (local or via JetBrains MCP), sandboxed code execution, vector search backends, and persistent caching.

Data flows from user interactions through the presenter/controller into workflow graphs that invoke tools—filesystem operations, web search, document retrieval, or LLM calls—accumulating results into a shared context stack that feeds back into the UI. The system also exposes its capabilities as an MCP server, allowing external tools (like IDEs) to invoke its workflows.

## 3. Subsystem Map

| Module | Responsibility | Anchor Entry Points |
|--------|----------------|---------------------|
| `app/` | Interactive UI, state management, and user event handling | `app/main.py` (bootstrap), `app/presenter.py` (interactions), `app/state.py` (context) |
| `core/workflows/` | LangGraph-based agent workflows for planning, implementation, research, and context building | `core/workflows/build_context.py`, `core/workflows/implement_task.py`, `core/workflows/plan_task.py` |
| `core/container.py` | Service locator and LLM factory with cost tracking and model mode switching | `core/container.py` (AgentContainer) |
| `core/mcp_clients/` | Filesystem abstraction over local disk or JetBrains IDE via MCP | `core/mcp_clients/filesystem/` |
| `core/agent_tools.py` | Tool registry exposing search, sandbox, and skills to agent workflows | `core/agent_tools.py` (build_tools) |
| `core/sandbox/` | Isolated code execution environments (macOS sandbox-exec, Docker placeholder) | `core/sandbox/macos.py`, `core/sandbox/base.py` |
| `search/` | Hybrid vector + text search over code and documents with embeddings and reranking | `search/indexer.py` (code), `search/document_indexer.py` (docs), `search/search.py` (retrieval) |
| `search/db/` | PostgreSQL/pgvector persistence with Alembic migrations | `search/db/models.py`, `search/db/repository.py` |
| `lib/` | Shared utilities: tree parsing, code extraction, token counting, logging | `lib/tree_parser.py`, `lib/treesitter_extractor.py`, `lib/helpers.py` |

## 4. Key Concepts

- **Context Stack** — Ordered collection of entries (files, summaries, conversation turns) that forms the working memory for LLM prompts
- **Workflow** — A LangGraph state machine defining multi-step agent behavior with tool loops and human-in-the-loop decisions
- **AgentContainer** — Dependency injection root holding configured LLM instances, filesystem clients, search managers, and cost tracker
- **Model Mode** — Runtime toggle between standard and high-quality LLM configurations affecting cost and capability
- **Hybrid Search** — Combined BM25 text search and vector similarity with cross-encoder reranking for code/document retrieval
- **Sandbox** — Restricted execution environment for running generated code safely
- **Skill** — Reusable prompt template or instruction set loaded from filesystem and injected into agent context

## 5. Architectural Constraints & Integrations

- **Multi-provider LLM dependency**: Requires OpenRouter, OpenAI, Google GenAI, or DeepSeek API keys; designed to switch providers at runtime via container configuration
- **MCP protocol integration**: Exposes tools via SSE endpoints for IDE consumption and consumes filesystem operations from JetBrains MCP server
- **Vector database duality**: Supports both Chroma (local, POC) and PostgreSQL/pgvector with ParadeDB extensions (production) for embeddings
- **Sandbox platform limitation**: macOS sandbox-exec fully implemented; Docker sandbox is stubbed
- **Deployment**: Packaged as Docker Compose stack with ParadeDB; UI runs as embedded NiceGUI within FastAPI
- **Cost tracking**: All LLM invocations accumulate costs in a shared tracker surfaced to the UI
- **Event-driven UI updates**: Presenter and views communicate through a typed event bus, not direct callbacks