# ⚛️ Proton Server & REST / SSE API Reference `v2.6.4`

[![Version](https://img.shields.io/badge/version-2.6.4-blue.svg?style=for-the-badge&logo=appveyor)](https://github.com/arjunmdivekar-afk/Proton)
[![API Protocol](https://img.shields.io/badge/API-REST%20%7C%20SSE-orange.svg?style=for-the-badge)]()
[![Swagger](https://img.shields.io/badge/Swagger_UI-%2Fdocs-brightgreen.svg?style=for-the-badge)](http://127.0.0.1:8787/docs)

<div align="center">

| [📖 **README**](README.md) | [🛡️ **Security Policy**](SECURITY.md) | [📚 **REST & SSE API Docs**](API-docs.md) | [⚖️ **License**](LICENSE) |
|---|---|---|---|

</div>

> **Proton Server** decouples the Proton Core intelligence engine from the terminal CLI, exposing an asynchronous, high-performance REST and Server-Sent Events (SSE) gateway. This enables web frontends, browser extensions, desktop applications, IDE plugins (VS Code / JetBrains), and external agent orchestrators to communicate directly with Proton.

```text
                    ┌─────────────────────┐
                    │    Proton Core      │
                    │                     │
                    │ Agent Engine        │
                    │ Max Agent           │
                    │ Tasks               │
                    │ Memory              │
                    │ RAG                 │
                    │ GraphRAG            │
                    │ Tools               │
                    │ Security            │
                    │ Providers           │
                    └──────────┬──────────┘
                               │
                        Proton Server (FastAPI / Uvicorn)
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
           CLI/TUI          Web UI          Other Apps / IDEs
              │                │                │
              ▼                ▼                ▼
         Terminal          Browser          API Client
```

---

## 📑 Table of Contents
- [🚀 Quick Start](#-quick-start)
- [🌐 Interactive API Documentation](#-interactive-api-documentation)
- [📡 API Subsystems](#-api-subsystems)
  - [1. Chat & Streaming Token Generation (`/v1/chat`)](#1-chat--streaming-token-generation-v1chat)
  - [2. Max-Level Autonomous Agent Lifecycle (`/v1/agents/run`)](#2-max-level-autonomous-agent-lifecycle-v1agentsrun)
  - [3. Persistent Engineering Tasks (`/v1/tasks`)](#3-persistent-engineering-tasks-v1tasks)
  - [4. Project Knowledge Graph & GraphRAG (`/v1/graph`)](#4-project-knowledge-graph--graphrag-v1graph)
  - [5. Categorized Domain Memory (`/v1/memory`)](#5-categorized-domain-memory-v1memory)
  - [6. Local Knowledge Base & Hybrid RAG (`/v1/rag`)](#6-local-knowledge-base--hybrid-rag-v1rag)
  - [7. Security Verification & Defense Testing (`/v1/security`)](#7-security-verification--defense-testing-v1security)
  - [8. Deterministic Sandbox Tool Execution (`/v1/tools`)](#8-deterministic-sandbox-tool-execution-v1tools)
  - [9. Deep Repository & Architecture Inspection (`/v1/inspect`)](#9-deep-repository--architecture-inspection-v1inspect)
  - [10. Multi-Dimensional Model Benchmark (`/v1/benchmark`)](#10-multi-dimensional-model-benchmark-v1benchmark)
  - [11. Models, Providers & LAN Connections (`/v1/models`, `/v1/connections`)](#11-models-providers--lan-connections-v1models-v1connections)
  - [12. Server Telemetry & Health (`/v1/health`)](#12-server-telemetry--health-v1health)
- [🔒 Error Handling & Status Codes](#-error-handling--status-codes)
- [🐍 Python SDK Integration Example](#-python-sdk-integration-example)

---

## 🚀 Quick Start

### Start Proton Server
```bash
# Start server (auto-binds to Localhost AND Connected WiFi network)
proton server

# Host on Connected WiFi / LAN for other devices on the network
proton server --host lan
# or
proton server --wifi --port 8787

# Bind to custom network interface and port
proton server --host 0.0.0.0 --port 8787 --reload
```

When started, Proton automatically detects your WiFi/LAN IP (e.g. `192.168.16.120:8787`) and provides live endpoints accessible by any device on the same WiFi network.

---

## 🌐 Interactive API Documentation

When Proton Server is running, open the interactive browser documentation:
- **Swagger UI Playground**: [http://127.0.0.1:8787/docs](http://127.0.0.1:8787/docs) — Explore schemas, test live requests, and view Python code examples directly under each operation bar.
- **ReDoc Technical Reference**: [http://127.0.0.1:8787/redoc](http://127.0.0.1:8787/redoc)
- **OpenAPI 3.1 JSON Specification**: [http://127.0.0.1:8787/openapi.json](http://127.0.0.1:8787/openapi.json)

---

## 📡 API Subsystems

### 1. Chat & Streaming Token Generation (`/v1/chat`)

Generate conversational AI responses with live token streaming (Server-Sent Events) and automatic system context enrichment (live datetime, workspace path, categorized memory).

#### `POST /v1/chat`

**Request Body (`application/json`):**
```json
{
  "messages": [
    {"role": "user", "content": "Explain how GraphRAG impact analysis calculates blast radius."}
  ],
  "model": "llama-3.2-1b-instruct",
  "stream": true,
  "temperature": 0.7,
  "use_memory": true
}
```

#### 🐍 Python Example — Streaming Tokens (SSE with `httpx`):
```python
import httpx
import json

url = "http://127.0.0.1:8787/v1/chat"
payload = {
    "messages": [
        {"role": "user", "content": "Explain how GraphRAG impact analysis calculates blast radius."}
    ],
    "stream": True,
    "temperature": 0.7,
    "use_memory": True
}

with httpx.stream("POST", url, json=payload, timeout=60.0) as response:
    print("Connected! Streaming tokens:")
    for line in response.iter_lines():
        if line.startswith("data: ") and line != "data: [DONE]":
            chunk = json.loads(line[6:])
            delta = chunk["choices"][0]["delta"].get("content", "")
            print(delta, end="", flush=True)
    print("\n[Stream Finished]")
```

#### 💻 cURL Example:
```bash
curl -N -X POST http://127.0.0.1:8787/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello Proton!"}], "stream": true}'
```

---

### 2. Max-Level Autonomous Agent Lifecycle (`/v1/agents/run`)

Launch Proton's 10-stage autonomous software engineering agent on a complex goal:
`Understand ➔ Inspect ➔ Plan ➔ Approve ➔ Tools ➔ Modify ➔ Test ➔ Review ➔ Self-Heal ➔ Report`

#### `POST /v1/agents/run`

**Request Body (`application/json`):**
```json
{
  "goal": "Refactor authentication middleware to support JWT validation and run test suite",
  "auto_approve": true,
  "max_steps": 30
}
```

#### 🐍 Python Example:
```python
import requests

url = "http://127.0.0.1:8787/v1/agents/run"
payload = {
    "goal": "Refactor authentication module to support JWT validation and run tests",
    "auto_approve": True,
    "max_steps": 30
}

response = requests.post(url, json=payload, timeout=300.0)
report = response.json()
print("Agent Status:", report["status"])
print("Files Modified:", report["files_modified"])
print("Tests Passed:", report["tests_passed"])
print("Audit Report:", report["audit_report_path"])
```

---

### 3. Persistent Engineering Tasks (`/v1/tasks`)

Manage long-running development tasks with persistent disk checkpoints in `~/.proton/tasks/`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/v1/tasks` | Create a new persistent development task |
| `GET` | `/v1/tasks` | List all tracked tasks (optionally filtered by `?status=IN_PROGRESS`) |
| `GET` | `/v1/tasks/{id}` | Inspect complete task checkpoints (plan, files, commands, errors) |
| `POST` | `/v1/tasks/{id}/run` | Execute or resume an active task |
| `POST` | `/v1/tasks/{id}/pause` | Pause task execution and freeze state |
| `DELETE` | `/v1/tasks/{id}` | Permanently delete a task record |

#### 🐍 Python Example — Full Task Lifecycle:
```python
import requests

# 1. Create task
create_res = requests.post("http://127.0.0.1:8787/v1/tasks", json={
    "title": "ESP32 Camera Streaming Server",
    "goal": "Build an ESP32 web server that streams MJPEG video over WiFi on port 80",
    "auto_approve": False,
    "max_steps": 30
})
task = create_res.json()
task_id = task["id"]
print(f"Created Task {task_id}: {task['status']}")

# 2. List tasks
tasks = requests.get("http://127.0.0.1:8787/v1/tasks").json()
print(f"Total Persistent Tasks: {tasks['total']}")

# 3. Run task
run_res = requests.post(f"http://127.0.0.1:8787/v1/tasks/{task_id}/run", params={"auto_approve": True})
print("Execution Result:", run_res.json()["status"])
```

---

### 4. Project Knowledge Graph & GraphRAG (`/v1/graph`)

Static AST relationship extraction and Change Impact Analysis ("What will break if I modify this symbol?").

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/graph/impact?symbol={symbol}` | Calculate change impact score and blast radius |
| `GET` | `/v1/graph/callers?symbol={symbol}` | Find all functions and modules calling the target symbol |
| `GET` | `/v1/graph/tests?symbol={symbol}` | Find all automated tests covering the target symbol |
| `GET` | `/v1/graph/stats` | Retrieve total nodes, edges, classes, and function counts |
| `POST` | `/v1/graph/build` | Scan codebase and rebuild AST graph in SQLite |

#### 🐍 Python Example — Change Impact Analysis:
```python
import requests

url = "http://127.0.0.1:8787/v1/graph/impact"
params = {"symbol": "validate_path"}

response = requests.get(url, params=params)
data = response.json()
print(f"Target Symbol: {data['symbol']}")
print(f"Blast Radius Score: {data['total_blast_radius']}")
print("Direct Callers:", data["direct_callers"])
print("Tests Affected:", data["tests_affected"])
```

---

### 5. Categorized Domain Memory (`/v1/memory`)

Stores structured memories across 7 explicit partitions: `PROJECT`, `DECISION`, `PREFERENCE`, `FACT`, `TASK`, `USER`, and `SESSION`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/memory` | List memories (optionally filtered by `?memory_type=DECISION`) |
| `POST` | `/v1/memory` | Add a structured memory record |
| `POST` | `/v1/memory/search` | Search memories by keyword or semantic query |
| `DELETE` | `/v1/memory/{id}` | Delete a specific memory item |
| `DELETE` | `/v1/memory` | Clear all memories or memories in a category |

#### 🐍 Python Example:
```python
import requests

# Add structured decision memory
requests.post("http://127.0.0.1:8787/v1/memory", json={
    "content": "Use LM Studio on LAN 192.168.16.120 as primary inference server.",
    "memory_type": "DECISION",
    "confidence": 1.0
})

# Search memory
matches = requests.post("http://127.0.0.1:8787/v1/memory/search", json={
    "query": "primary inference server",
    "limit": 5
}).json()

for m in matches:
    print(f"- [{m['type']}] #{m['id']}: {m['content']}")
```

---

### 6. Local Knowledge Base & Hybrid RAG (`/v1/rag`)

In-process hybrid vector and BM25 store backed by SQLite (`~/.proton/rag_index.db`).

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/v1/rag/search` | Hybrid vector & BM25 document query |
| `POST` | `/v1/rag/index` | Index codebase files into SQLite vector store |
| `GET` | `/v1/rag/status` | Get total indexed document chunk counts |

#### 🐍 Python Example:
```python
import requests

url = "http://127.0.0.1:8787/v1/rag/search"
payload = {
    "query": "hybrid vector BM25 similarity scoring",
    "top_k": 3,
    "min_similarity": 0.25
}

response = requests.post(url, json=payload)
results = response.json()
print(f"Total Matches: {results['total']}")
for r in results["results"]:
    print(f"- [{r['score']:.2f}] {r['citation']}")
```

---

### 7. Security Verification & Defense Testing (`/v1/security`)

Automated live defense testing against 8 threat vectors.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/security` | Get active security posture, approval mode, and blacklist |
| `POST` | `/v1/security/test` | Execute automated 8-stage live defense verification battery |
| `GET` | `/v1/security/audit` | Static workspace secret and permission scan |

#### 🐍 Python Example:
```python
import requests

url = "http://127.0.0.1:8787/v1/security/test"
response = requests.post(url)
data = response.json()
print(f"Security Score: {data['security_score']} / 100 — {data['verdict']}")
for check in data["checks"]:
    status = "PASS ✓" if check["passed"] else "FAIL ✗"
    print(f"[{status}] {check['name']}: {check['risk_mitigated']}")
```

---

### 8. Deterministic Sandbox Tool Execution (`/v1/tools`)

Execute sandboxed tools (`read_file`, `write_file`, `edit_file`, `list_directory`, `search_code`, `shell_execute`, `git_status`, `git_diff`, `duckduckgo_search`, `fetch_web_page`) with boundary checks.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/tools` | List registered tools, risk ratings, and JSON Schemas |
| `POST` | `/v1/tools/execute` | Securely execute a tool inside the sandbox |

#### 🐍 Python Example:
```python
import requests

url = "http://127.0.0.1:8787/v1/tools/execute"
payload = {
    "tool": "read_file",
    "arguments": {"path": "pyproject.toml"}
}

response = requests.post(url, json=payload)
result = response.json()
print("Success:", result["success"])
print("File Content:\n", result["result"][:200])
```

---

### 9. Deep Repository & Architecture Inspection (`/v1/inspect`)

Structural inspection across languages, frameworks, architecture, dependencies, git status, tests, and performance.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/inspect` | Full structural inspection report |
| `GET` | `/v1/inspect/architecture` | Architectural patterns, layers, and entry points |
| `GET` | `/v1/inspect/security` | Vulnerability scan and exposed secret checks |
| `GET` | `/v1/inspect/dependencies` | Manifests, direct dependencies, and package manager |
| `GET` | `/v1/inspect/tests` | Test framework and test file discovery |
| `GET` | `/v1/inspect/performance` | Large file scanner and repo size footprint |

#### 🐍 Python Example:
```python
import requests

url = "http://127.0.0.1:8787/v1/inspect/architecture"
response = requests.get(url)
arch = response.json()
print(f"Detected Pattern: {arch['pattern']}")
print(f"Architectural Layers: {arch['layers']}")
print(f"Entry Points: {arch['entry_points']}")
```

---

### 10. Multi-Dimensional Model Benchmark (`/v1/benchmark`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/v1/benchmark/run?quick=false` | Execute 8-dimension capability benchmark |
| `GET` | `/v1/benchmark/history` | Retrieve historical benchmark evaluations |

#### 🐍 Python Example:
```python
import requests

url = "http://127.0.0.1:8787/v1/benchmark/run"
response = requests.post(url, params={"quick": False}, timeout=180.0)
data = response.json()
print(f"Overall Rating: [{data['overall_grade']}] {data['overall_score']} / 100")
print(f"Speed: {data['tokens_per_second']:.1f} tokens/sec")
print(f"Agent Readiness: {data['agent_readiness']}")
```

---

### 11. Models, Providers & LAN Connections (`/v1/models`, `/v1/connections`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/models` | List dynamically discovered models from active provider |
| `GET` | `/v1/connections` | List configured local and LAN AI endpoints |
| `POST` | `/v1/connections/switch` | Switch active inference connection (e.g. `server-1`) |
| `POST` | `/v1/models/switch` | Switch active model ID |

#### 🐍 Python Example:
```python
import requests

# List models
models_res = requests.get("http://127.0.0.1:8787/v1/models").json()
print("Active Model:", models_res["active_model"])
for m in models_res["models"]:
    print(f"- {m['id']}")

# Switch active connection
requests.post("http://127.0.0.1:8787/v1/connections/switch", json={"connection_id": "server-1"})
```

---

### 12. Server Telemetry & Health (`/v1/health`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/health` | Server status, version, uptime, and active connection |
| `GET` | `/v1/info` | Endpoint capability manifest and Swagger doc links |

#### 🐍 Python Example:
```python
import requests

response = requests.get("http://127.0.0.1:8787/v1/health")
health = response.json()
print(f"Proton Server: {health['status']} (v{health['version']})")
print(f"Uptime: {health['uptime_seconds']}s")
print(f"Active Provider: {health['provider_type']} at {health['base_url']}")
```

---

## 🔒 Error Handling & Status Codes

Proton Server returns standard HTTP status codes and structured JSON errors:

| Status Code | Reason | Example Response |
|---|---|---|
| `200 OK` | Successful request | Normal JSON payload or SSE stream |
| `400 Bad Request` | Invalid arguments / parameter validation | `{"detail": "Invalid tool arguments"}` |
| `404 Not Found` | Resource not found | `{"detail": "Task 'task-123' not found."}` |
| `403 Forbidden` | Sandbox violation or permission denied | `{"detail": "Access outside workspace is denied."}` |
| `503 Service Unavailable` | AI provider (LM Studio / Ollama) unreachable | `{"detail": "Cannot reach AI inference runtime..."}` |
| `500 Internal Error` | Unhandled server error | `{"detail": "Inference error: ..."}` |

---

## 🐍 Python SDK Integration Example

Here is a full Python client script showing how to interact with Proton Server end-to-end:

```python
import httpx
import json

BASE_URL = "http://127.0.0.1:8787"

def main():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Health Check
        health = client.get("/v1/health").json()
        print(f"Connected to Proton v{health['version']} [{health['active_model']}]")

        # 2. Add Decision Memory
        client.post("/v1/memory", json={
            "content": "API client initialized successfully.",
            "memory_type": "SESSION"
        })

        # 3. Query GraphRAG Blast Radius
        impact = client.get("/v1/graph/impact", params={"symbol": "validate_path"}).json()
        print(f"Blast Radius for 'validate_path': {impact['total_blast_radius']}")

        # 4. Stream Chat Completion (SSE)
        print("\nStreaming Chat Response:")
        with client.stream("POST", "/v1/chat", json={
            "messages": [{"role": "user", "content": "What are Proton's core capabilities?"}],
            "stream": True
        }) as stream:
            for line in stream.iter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    chunk = json.loads(line[6:])
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    print(delta, end="", flush=True)
        print("\n")

if __name__ == "__main__":
    main()
```
