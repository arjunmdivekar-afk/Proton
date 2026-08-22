# Proton Architecture

Proton is designed with a strict interface-driven, modular architecture separating CLI/TUI presentation, agent orchestration, model abstraction, security policies, deterministic tool execution, local hybrid RAG, and multi-tier memory.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                              PROTON CLI & TUI                          │
│     Interactive REPL (Rich + prompt_toolkit) | Non-Interactive (JSON)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                               AGENT ENGINE                             │
│       Context Assembler | Task Planner | Multi-step Reasoning Loop     │
└───────┬───────────────────────────┬────────────────────────────┬───────┘
        │                           │                            │
        ▼                           ▼                            ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ MODEL PROVIDERS  │      │ SECURITY ENGINE  │      │  TOOL REGISTRY   │
│  - LM Studio     │      │  - Strict Policy │      │  - Filesystem    │
│  - Ollama        │      │  - HITL Approval │      │  - Shell Exec    │
│  - OpenAI-Compat │      │  - Redaction     │      │  - Git & Coding  │
│  - Router & Ping │      │  - Audit Logger  │      │  - RAG & Memory  │
└──────────────────┘      └──────────────────┘      └──────────────────┘
        │                           │                            │
        └───────────────────────────┼────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                              LOCAL STORAGE                             │
│     SQLite DB (Sessions, History) | SQLite Vector & Hybrid RAG Store   │
│     Persistent Memory (Project/User/Session) | Audit Trail             │
└────────────────────────────────────────────────────────────────────────┘
```

## Core Subsystems

### 1. Connection Manager (`proton.connection`)
- Supports local (`127.0.0.1:1234`) and remote LAN IPs (`192.168.1.50:1234`) for LM Studio, Ollama, and OpenAI-compatible inference servers.
- Live TCP socket connectivity probe, HTTP `/v1/models` retrieval, round-trip latency benchmarking, and error remediation.
- Named connection profiles saved to `~/.proton/connections.yaml`.

### 2. Model Provider Layer (`proton.providers`)
- `ModelProvider` abstract base interface.
- Standardized streaming chat completions (`stream_chat`), non-streaming completions (`chat_complete`), and vector embeddings (`embed`).
- Dynamic model discovery from `/v1/models`.

### 3. Security & Approvals (`proton.security`)
- Strict Human-in-the-Loop (Level 1) approval engine (`Allow Once`, `Allow Session`, `Deny`).
- Filesystem sandbox preventing path traversal outside the active workspace.
- Automatic secret and API key redaction in logs, prompts, and output.
- SQLite audit logging (`~/.proton/audit.db`).

### 4. Deterministic Tools (`proton.tools`)
- Structured tools with Pydantic argument validation and JSON Schema generation.
- Suite includes: `read_file`, `write_file`, `edit_file`, `list_directory`, `search_code`, `shell_execute`, `git_status`, `git_diff`, `git_log`, `git_commit`, `apply_patch`, `run_tests`, `rag_search`, `rag_index`, `memory_add`, `memory_search`.

### 5. Local Hybrid RAG & Vector Store (`proton.rag`)
- Parent-child document chunking with content hashing (SHA256) for incremental updates.
- In-process SQLite hybrid vector store combining vector cosine similarity with BM25 keyword matching.
- Verified source citations linking responses directly to repository files and line numbers.

### 6. Memory & Sessions (`proton.memory` & `proton.sessions`)
- Persistent SQLite conversation history (`~/.proton/proton.db`), resumable sessions, and export to Markdown/JSON.
- Multi-tier memory store (Session, Project, User) for remembering rules, preferences, and architectural patterns.
