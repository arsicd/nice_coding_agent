# Nice Coding Agent

An AI-powered development assistant that helps you understand, plan, implement, research, and document code in your own projects — all through a conversational web UI.

Nice Coding Agent runs LLM agent workflows that can read and write your local filesystem, search your code and documents with hybrid retrieval, run sandboxed code, and browse the web. It's built in Python with [NiceGUI](https://nicegui.io/) for the frontend and LangChain/LangGraph for agent orchestration.

## Features

- **Conversational web UI** — interact with agent workflows from a single-page NiceGUI interface, with live streaming of model output and per-session cost tracking.
- **Agent workflows** — dedicated flows for planning, implementing, researching, browsing, and building context, each a LangGraph state machine that runs multi-round LLM conversations with tool calls.
- **Hybrid code & document search** — BM25 full-text + pgvector ANN retrieval with cross-encoder reranking, backed by PostgreSQL (ParadeDB + pgvector).
- **Filesystem access** — read, write, list, and edit files in your project, with gitignore-aware filtering. Supports both local I/O and JetBrains IDE integration over MCP.
- **Sandboxed execution** — agent-generated code runs in an isolated macOS sandbox for safe verification (Docker backend planned).
- **Pluggable LLM providers** — works with OpenAI-compatible, Google Gemini, DeepSeek, Kimi, and OpenRouter endpoints. Toggle between "standard" and "high" model tiers for cost-vs-quality control.
- **Web research** — external web search via the Exa API.

## Requirements

- [uv](https://docs.astral.sh/uv/) (for running the app)
- [Docker](https://docs.docker.com/get-docker/) (for the PostgreSQL database)

## Getting Started

### 1. Start the database

This runs a pre-built PostgreSQL image (ParadeDB + pgvector) for hybrid search:

```bash
docker run -d \
  --name agent_postgres \
  -p 5432:5432 \
  -v agent_pgdata:/var/lib/postgresql \
  --shm-size=1g \
  ghcr.io/arsicd/nice_parade:latest
```

### 2. Run the app

```bash
uvx --from git+https://github.com/arsicd/nice_coding_agent agent
```

The web UI will be available in your browser once the app starts.

### Stopping and restarting

The database keeps running in the background. To stop it:

```bash
docker stop agent_postgres
```

To start it again later (your data is preserved in the `agent_pgdata` volume):

```bash
docker start agent_postgres
```

## Configuration

LLM providers, API keys, and other settings are configured through environment variables. You'll need at least one LLM provider configured (OpenAI-compatible, Gemini, DeepSeek, Kimi, or OpenRouter), and an Exa API key if you want web search.

## How It Works

The UI follows a Presenter–Controller–State pattern coordinated by an async event bus, which is the sole channel between the interface and application logic. User actions flow through a core router into LangGraph agent workflows. All LLM calls are routed through a central agent container for consistent model selection, streaming, and cost tracking, and all filesystem changes are proxied through an MCP client rather than written directly.

Under the workflows sit two main subsystems: an LLM container managing model instances and provider abstraction, and a hybrid search engine combining BM25, vector search, and reranking over PostgreSQL.

For a deeper technical breakdown, see the project overview document.

## Tech Stack

- **Frontend:** NiceGUI (FastAPI + Vue/Quasar)
- **Orchestration:** LangChain / LangGraph
- **Database:** PostgreSQL with ParadeDB extensions + pgvector (Alembic migrations)
- **Embeddings & reranking:** sentence-transformers (Jina Code, Nomic) and mxbai-rerank / Jina
- **Code parsing:** Tree-sitter (Python, JavaScript, TypeScript, Go)
- **Web search:** Exa API

## License

See the LICENSE file in this repository.