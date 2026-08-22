# ⚛️ Proton — Enterprise Autonomous AI CLI & Agent Platform `v2.4.4`

[![Version](https://img.shields.io/badge/version-2.4.4-blue.svg?style=for-the-badge&logo=appveyor)](https://github.com/arjunmdivekar-afk/Proton)
[![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg?style=for-the-badge)]()
[![Architecture](https://img.shields.io/badge/architecture-GraphRAG%20%7C%20Stateful%20Tasks%20%7C%20Verified%20Security-orange.svg?style=for-the-badge)]()

> **Proton** is an enterprise-grade, provider-neutral AI CLI assistant, autonomous software engineering agent, stateful task manager, code graph intelligence engine (GraphRAG), categorized memory system, automated security verification suite, multi-dimensional model benchmark battery, keyboard-first terminal web browser, and live market intelligence platform. Designed from first principles for developers, DevOps engineers, and researchers operating directly in terminal environments.

```text
                                   ⚛️ PROTON ARCHITECTURE
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                    TERMINAL TUI / CLI                                     │
│   proton • proton task • proton graph • proton security • proton benchmark • proton agent │
├─────────────────────────┬───────────────────────────────┬─────────────────────────────────┤
│    REASONING & AGENTS   │       CODE INTELLIGENCE       │       SECURITY & GOVERNANCE     │
│  • 10-Stage Max Agent   │  • AST Code Knowledge Graph   │  • Automated Defense Testing    │
│  • Task Checkpointing   │  • Blast Radius Impact Engine │  • Filesystem Sandbox Boundary  │
│  • Categorized Memory   │  • Hybrid BM25 / Vector RAG   │  • Secret Token Redaction       │
│  • Model Benchmark Suite│  • Deep Repo Inspector        │  • Strict Approval Guardrails   │
├─────────────────────────┴───────────────────────────────┴─────────────────────────────────┤
│                             LOCAL & LAN INFERENCE RUNTIMES                                │
│          LM Studio (LAN IP / Localhost) • Ollama • OpenAI-Compatible Gateways             │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎥 Introduction to Proton

https://github.com/user-attachments/assets/ad1aaa4e-ec61-4247-8d73-e94580b5b250

> 🎬 *Live walkthrough of Proton's autonomous agent lifecycle, terminal browser, live stock intelligence tracker, GraphRAG engine, explicit memory, and automated security verification suite.*

---

## 📑 Table of Contents
- [🎥 Introduction Video](#-introduction-to-proton)
- [✨ Key Features](#-key-features)
- [📦 Quick Installation](#-quick-installation)
- [🚀 60-Second Quick Start](#-60-second-quick-start)
- [💻 Deep CLI Subsystem Reference](#-deep-cli-subsystem-reference)
  - [1. Security Verification & Live Defense Testing (`proton security`)](#1-security-verification--live-defense-testing-proton-security)
  - [2. Multi-Dimensional LLM Benchmark Battery (`proton benchmark`)](#2-multi-dimensional-llm-benchmark-battery-proton-benchmark)
  - [3. Project Knowledge Graph & GraphRAG (`proton graph`)](#3-project-knowledge-graph--graphrag-proton-graph)
  - [4. Deep Repository & Codebase Inspection (`proton inspect`)](#4-deep-repository--codebase-inspection-proton-inspect)
  - [5. Persistent Engineering Task Manager (`proton task`)](#5-persistent-engineering-task-manager-proton-task)
  - [6. Explicit Categorized Domain Memory (`proton memory`)](#6-explicit-categorized-domain-memory-proton-memory)
  - [7. Max-Level Autonomous Agent Lifecycle (`proton agent`)](#7-max-level-autonomous-agent-lifecycle-proton-agent)
  - [8. Interactive AI Assistant & Session Resumption (`proton`)](#8-interactive-ai-assistant--session-resumption-proton)
  - [9. Keyboard-First Terminal Web Browser (`proton browser`)](#9-keyboard-first-terminal-web-browser-proton-browser)
  - [10. Live Market Intelligence & Stock Charts (`proton stock`)](#10-live-market-intelligence--stock-charts-proton-stock)
  - [11. Host Diagnostics & Resource Telemetry (`proton doctor --sys`)](#11-host-diagnostics--resource-telemetry-proton-doctor---sys)
  - [12. Local Knowledge Base & Hybrid RAG (`proton rag`)](#12-local-knowledge-base--hybrid-rag-proton-rag)
  - [13. Multi-Provider Connection Management (`proton connection`)](#13-multi-provider-connection-management-proton-connection)
- [🧠 Recommended Models & Hardware Matrix](#-recommended-models--hardware-matrix)
  - [1. Small Models (1B to 10B Parameters)](#1-small-models-1b-to-10b-parameters--fast-local-execution)
  - [2. Medium Models (10B to 100B Parameters)](#2-medium-models-10b-to-100b-parameters--coding--deep-reasoning)
  - [3. Large Models (100B+ Frontier MoE)](#3-large-models-100b-parameters--frontier-moe--enterprise-agents)
  - [⚡ Hardware Requirements Matrix](#-hardware-requirements-matrix)
- [⌨️ REPL Slash Command Matrix](#️-repl-slash-command-matrix)
- [🎨 Visual Styling & High-Contrast TUI Engine](#-visual-styling--high-contrast-tui-engine)
- [🔒 Enterprise Security & Sandboxing Architecture](#-enterprise-security--sandboxing-architecture)
- [📁 Project Directory Topology](#-project-directory-topology)
- [📜 License](#-license)

---

## ✨ Key Features

- **🛡️ Continuous Security Verification (`proton security test` / `proton security audit`)**: Transition beyond passive security. Automated real-time defensive verification suite continuously validating guardrails against **path traversal, command injection, secret leakage, malicious tool arguments, prompt injection, workspace escapes, unauthorized network access, and dangerous shell commands** with scored verification reports (100/100).
- **⚡ 8-Dimension LLM Benchmark Battery (`proton benchmark`)**: Evaluate local and LAN models across **Latency (TTFT), Streaming Throughput (tok/s), Context Retention (needle-in-haystack), Tool Calling (JSON schema), RAG Synthesis, Coding Quality (Python AST validation), Planning, and Error Self-Healing** with letter grading (`A+` to `F`) and agent readiness badges.
- **🌐 Project Knowledge Graph & GraphRAG (`proton graph`)**: Full AST static structural relationship extractor indexing `Function ➔ Calls ➔ Function`, `Class ➔ Inherits ➔ Class`, `Module ➔ Imports ➔ Module`, and `Test ➔ Tests ➔ Function`. Answers *"What will break if I change this function?"* with exact recursive blast-radius impact analysis.
- **🧠 Explicit Categorized Domain Memory (`proton memory`)**: Replaces disorganized chat history dumps with 7 structured memory partitions: **`PROJECT`**, **`DECISION`**, **`PREFERENCE`**, **`FACT`**, **`TASK`**, **`USER`**, and **`SESSION`**.
- **🔍 Deep Repository & Architecture Inspector (`proton inspect`)**: Instantly inspect languages, frameworks, dependencies, design patterns, entry points, test suites, git status, docs, environment, security vulnerabilities, and performance bottlenecks across any unfamiliar codebase.
- **📋 Stateful Engineering Task Manager (`proton task`)**: Isolates complex multi-hour development projects from ephemeral chat. Checkpoints **Goal, Step-by-Step Plan, Progress %, Modified Files, Executed Shell Commands, Tool Invocations, Errors, Approvals, and Test Results** to disk (`~/.proton/tasks/`) with pause/resume capabilities.
- **🤖 Max-Level Autonomous Agent (`proton agent`)**: 10-stage autonomous lifecycle (`Understand Task ➔ Inspect Repo ➔ Create Plan ➔ Ask Approval ➔ Use Tools ➔ Modify Files ➔ Run Tests ➔ Review Changes ➔ Fix Failures ➔ Generate Report`) with self-healing feedback loops.
- **🌐 Model & Provider Neutral**: First-class zero-friction support for **LM Studio** (local and LAN IP `http://192.168.x.x:1234`), **Ollama**, and any OpenAI-compatible inference gateway.
- **🌍 Proton Terminal Web Browser (`proton browser`)**: Full keyboard-first browser with live DuckDuckGo web search, numbered interactive links `[1-50]`, multi-hop page navigation, and embedded **Proton AI Copilot** (`/browser --ai_mode`).
- **📈 Real-Time Stock Market Dashboard (`proton stock`)**: Live stock market tracker in **Indian Rupees (`₹`)** with 10-minute auto-refresh, 20 instruments per page across Indian NSE/BSE & Global tech leaders, high-resolution continuous vector price charts, and **Proton AI Stock Analyst**.
- **🖥️ Host Diagnostics & Resource Monitor (`proton doctor --sys`)**: Live hardware telemetry inspects CPU cores, live RAM utilization bars, disk partitions, host uptime, and network interfaces.
- **🧠 Hybrid Vector & BM25 Knowledge Retrieval (`proton rag`)**: In-process parent-child chunking with SQLite vector indexing (`~/.proton/knowledge/`) and dynamic code retrieval (`proton rag fetch-knowledge`).

---

## 📦 Quick Installation

### 1. Clone Repository
```bash
git clone https://github.com/arjunmdivekar-afk/Proton.git
cd Proton
```

### 2. Install in Editable Development Mode
```bash
pip install -e .
```

### 3. Verify Version
```bash
proton --version
# Output: Proton version 2.4.4
```

---

## 🚀 60-Second Quick Start

```bash
# 1. Verify system security defenses and scan repo for exposed secrets
proton security test
proton security audit

# 2. Connect to your local or LAN AI provider (LM Studio / Ollama)
proton connection

# 3. Benchmark your model's agent readiness across 8 capability dimensions
proton benchmark

# 4. Ingest project decisions and preferences into categorized memory
proton memory add "Use LM Studio on LAN 192.168.16.120 as primary inference server" --type DECISION
proton memory add "Format all Python code adhering to PEP 8" --type PREFERENCE
proton memory list

# 5. Build project AST knowledge graph and test blast radius
proton graph build
proton graph impact validate_path

# 6. Deeply inspect codebase architecture and dependencies
proton inspect

# 7. Create and run a stateful engineering task
proton task create "Auth Refactor" "Migrate authentication to JWT tokens with automated tests"
proton task run <task-id>

# 8. Launch interactive streaming assistant (or resume named session)
proton
proton --test

# 9. Launch terminal browser or live stock market tracker
proton browser "fastapi tutorial"
proton stock
```

---

## 💻 Deep CLI Subsystem Reference

### 1. Security Verification & Live Defense Testing (`proton security`)
Proton enforces security verification: live automated threat injection to verify that all protective guardrails are active and operating as expected.

```text
┌───────────── 🛡️ Proton Automated Security Defense Verification ─────────────┐
│ Target Workspace: C:\Users\arjun.divekar\Desktop\Proton                     │
│ Defense Checks Passed: 8 / 8   Security Score: 100 / 100                    │
│ Verification Verdict: 🛡️ Enterprise Secure — All Guardrails Verified        │
└─────────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────┬─────────┬────────────────────────────┐
│ Threat Vector                        │ Status  │ Mitigated Risk             │
├──────────────────────────────────────┼─────────┼────────────────────────────┤
│ Path Traversal Defense               │ PASS ✓  │ Blocked 5/5 traversal args │
│ Workspace Boundary Containment       │ PASS ✓  │ Boundary enforced strictly │
│ Command Injection & Chaining         │ PASS ✓  │ Classified as DESTRUCTIVE  │
│ Dangerous Shell Command Blacklist    │ PASS ✓  │ Intercepted 4/4 dangerous  │
│ Secret Leakage & Token Redaction     │ PASS ✓  │ Scrubbed 4/4 credentials   │
│ Malicious Tool Argument Grader       │ PASS ✓  │ Accurate risk levels       │
│ Prompt Injection & Jailbreak Filters │ PASS ✓  │ Intercepted 3/3 overrides  │
│ Unauthorized Network & Endpoints     │ PASS ✓  │ Confined to authorized LAN │
└──────────────────────────────────────┴─────────┴────────────────────────────┘
```

**Commands:**
```bash
# Execute automated defense test battery
proton security test

# Perform static workspace security audit (exposed keys, file permissions, CVEs)
proton security audit

# View security posture overview & active approval policy
proton security

# Output machine-readable JSON security report
proton security test --json
```

---

### 2. Multi-Dimensional LLM Benchmark Battery (`proton benchmark`)
Rigorously evaluates whether a connected model has the speed, context retention, and reasoning capabilities required for autonomous software engineering.

```text
┌──────────────── ⚡ Proton LLM & Provider Benchmark Results ─────────────────┐
│ Model: qwen2.5-coder-7b   Provider: lmstudio   Base URL: 192.168.16.120     │
│ TTFT: 140.2 ms   Throughput: 57.2 tokens/sec   Overall Rating: [A+] 96 / 100│
└─────────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────┬────────┬────────┬──────────┬─────────────┐
│ Capability Dimension             │ Result │ Score  │ Latency  │ Details     │
├──────────────────────────────────┼────────┼────────┼──────────┼─────────────┤
│ Latency & Speed                  │ PASS ✓ │  100%  │ 7730 ms  │ 57.2 tok/s  │
│ Coding & Syntax Correctness      │ PASS ✓ │  100%  │ 2240 ms  │ Valid AST   │
│ Tool Calling & JSON Routing      │ PASS ✓ │  100%  │ 3120 ms  │ Valid JSON  │
│ Context Retention (Needle)       │ PASS ✓ │  100%  │ 1890 ms  │ Found key   │
│ RAG Document Synthesis           │ PASS ✓ │  100%  │ 2100 ms  │ Grounded    │
│ Planning & Logical Breakdown     │ PASS ✓ │  100%  │ 2450 ms  │ 3-step plan │
│ Error Recovery & Debugging       │ PASS ✓ │  100%  │ 1980 ms  │ Fixed Error │
└──────────────────────────────────┴────────┴────────┴──────────┴─────────────┘

Autonomous Agent Readiness: 🥇 Elite Autonomous Agent Ready
```

**Commands:**
```bash
# Run full 8-stage benchmark suite
proton benchmark

# Run fast 3-stage benchmark (Speed, Coding, Tool Calling)
proton benchmark --quick

# View past benchmark runs and model performance trends
proton benchmark history

# Output machine-readable JSON benchmark report
proton benchmark --json
```

---

### 3. Project Knowledge Graph & GraphRAG (`proton graph`)
Extracts and traverses static AST relationships to answer complex architectural dependency questions:

```text
Function ──[CALLS]──➔ Function
Class    ──[INHERITS]──➔ Class
Module   ──[IMPORTS]──➔ Module
Test     ──[TESTS]──➔ Function
```

**Commands:**
```bash
# Build/rebuild SQLite AST structural graph
proton graph build

# Calculate Change Impact & Blast Radius ("What will break if I modify this function?")
proton graph impact validate_path
proton graph impact AgentEngine

# Discover all functions and modules that call a given symbol
proton graph callers validate_path

# Discover all automated unit tests covering a given symbol
proton graph tests validate_path

# View statistical overview of nodes, relationship edges, and call density
proton graph
```

---

### 4. Deep Repository & Codebase Inspection (`proton inspect`)
Builds a comprehensive structural understanding of any repository before generating code:

```text
PROJECT
├── Language detection
├── Framework detection
├── Dependencies
├── Architecture
├── Entry points
├── Test framework
├── Git status
├── Documentation
├── Environment
└── Potential problems
```

**Commands:**
```bash
# Run comprehensive repository inspection tree
proton inspect

# Run specialized security audit
proton inspect security

# Inspect architectural design patterns and structural layers
proton inspect architecture

# Inspect dependencies and package managers
proton inspect dependencies

# Discover test frameworks and coverage configuration
proton inspect tests

# Analyze repository disk footprint and locate large files (> 500 KB)
proton inspect performance

# Output machine-readable JSON for tooling
proton inspect --json
```

---

### 5. Persistent Engineering Task Manager (`proton task`)
Isolates multi-step engineering tasks from transient chat sessions. Every task maintains a stateful checkpoint on disk (`~/.proton/tasks/`):

```text
┌────────────────────────────────────────────────────────┐
│ PROTON PERSISTENT TASK CHECKPOINT                      │
├────────────────────────────────────────────────────────┤
│ • Goal & Scope              • Commands Executed        │
│ • Step-by-Step Plan         • Tool Invocation Logs     │
│ • Progress Percentage (%)   • Errors & Tracebacks      │
│ • Files Modified & Created  • Approvals Granted        │
│ • Automated Test Results    • Final Audit Report       │
└────────────────────────────────────────────────────────┘
```

**Commands:**
```bash
# Create a new persistent development task (Title and Goal)
proton task create "simple AI UI" "Create a simple web UI for an AI assistant"
proton task create "ESP32 Camera Server" "Build ESP32 camera server with streaming video"

# List all tracked tasks with status and progress percentages
proton task list
proton task list --status IN_PROGRESS

# Inspect detailed task record (Goal, Plan, Files, Commands, Tests, Errors)
proton task show <task-id>

# Run or continue an active task
proton task run <task-id>
proton task run <task-id> --auto-approve

# Pause task execution and freeze state
proton task pause <task-id>

# Resume a paused task from its latest checkpoint
proton task resume <task-id>

# Cancel or delete task
proton task cancel <task-id>
proton task delete <task-id>
```

---

### 6. Explicit Categorized Domain Memory (`proton memory`)
Structure persistent memories into explicit domain categories to eliminate context pollution:

| Category | Domain Scope | Example |
|---|---|---|
| **`PROJECT`** | Architecture constraints and repo layout | `ESP32 camera uses GPIO configuration X.` |
| **`DECISION`** | Architectural and technology choices | `Use LM Studio on LAN as primary local provider.` |
| **`PREFERENCE`** | Coding styles and formatting rules | `Prefer single-file Arduino examples.` |
| **`FACT`** | Domain knowledge, pinouts, and constants | `Camera frame buffer allocated in external PSRAM.` |
| **`TASK`** | Persistent goal and requirement reminders | `Always run pytest before pushing to main.` |
| **`USER`** | User role, background, and environment | `User prefers PowerShell on Windows.` |
| **`SESSION`** | Active conversation notes | `Working on branch feat-graphrag.` |

**Commands:**
```bash
# List all stored memories (or filter by category)
proton memory list
proton memory list --type DECISION

# Add categorized memory records
proton memory add "ESP32 camera uses GPIO configuration X" --type PROJECT
proton memory add "Use LM Studio as primary local provider" --type DECISION
proton memory add "Prefer single-file Arduino examples" --type PREFERENCE

# Search memory records by keyword
proton memory search "ESP32"

# Delete / Forget a specific memory record by ID
proton memory forget 3

# Export memories to Markdown or JSON
proton memory export
proton memory export --format json --file my_memory.json

# Clear memories (by category or all)
proton memory clear --type SESSION
```

---

### 7. Max-Level Autonomous Agent Lifecycle (`proton agent`)
Executes end-to-end software engineering tasks with a full **10-stage autonomous lifecycle**:

```text
Understand Task ➔ Inspect Repo ➔ Create Plan ➔ Ask Approval ➔ Use Tools
      ➔ Modify Files ➔ Run Tests ➔ Review Changes ➔ Fix Failures ➔ Generate Report
```

```bash
# Launch interactive autonomous agent on a goal
proton agent "Build a responsive sticky navigation header and write tests"

# Run unattended in auto-approve mode
proton agent "Refactor data service error handling and run pytest" --auto-approve

# Set maximum turn steps limit
proton agent "Fix failing test cases in auth module" -y --max-steps 30
```

---

### 8. Interactive AI Assistant & Session Resumption (`proton`)
Launch the interactive terminal session with live token streaming, tools, and stateful memory:
```bash
# Launch interactive REPL
proton

# Resume a previously saved conversation directly
proton --test
proton --auth_refactor

# Run non-interactive query
proton ask "Explain the architecture of this project"

# Output machine-readable JSON
proton ask "Generate quicksort in python" --json
```

**💾 Naming & Resuming Conversations (`Ctrl+T`):**
- Press **`Ctrl+T`** (or type `/exit`) anytime during your conversation.
- Proton prompts: `Save conversation as named session? (e.g. 'test'): `
- Enter any name (e.g. `test`).
- You can instantly resume that exact conversation with its entire message history anytime by running:
  ```bash
  proton --test
  ```

---

### 9. Keyboard-First Terminal Web Browser (`proton browser`)
Browse the web, query DuckDuckGo, navigate numbered links, and summarize pages using AI:
```bash
# Search DuckDuckGo and view results with interactive links
proton browser "python fastapi tutorial"

# Open a website URL directly
proton browser https://react.dev

# Launch browser with Proton AI Copilot enabled
proton browser --ai_mode
proton browser "machine learning papers" --ai_mode
```

**In-Browser Navigation Commands:**
| Command / Key | Description |
|---|---|
| `1` - `50` or `open 1` | Open the corresponding numbered link on the current page |
| `search <query>` | Search DuckDuckGo for new query |
| `open <url>` | Navigate directly to web URL |
| `links` | Display full table of all numbered hyperlinks on the page |
| `back` / `b` | Return to previous page in history |
| `forward` / `f` | Go forward in history |
| `reload` / `r` | Reload current page |
| `summarize` / `sum` | Use Proton AI to generate a structured executive summary of the page |
| `ask <question>` | Ask the AI Copilot questions about the active web page |
| `exit` / `q` | Exit browser |

---

### 10. Live Market Intelligence & Stock Charts (`proton stock`)
Real-time financial intelligence in **Indian Rupees (`₹`)** with 10-minute auto-refresh, 20 assets per page, and continuous sub-pixel price charts:
```bash
# Launch live stock dashboard
proton stock

# Inspect a specific Indian or Global stock directly
proton stock RELIANCE
proton stock TCS
proton stock INFY
proton stock AAPL
proton stock BTC-USD

# Open specific market category page
proton stock --page 1    # Indian Market & NIFTY 50 Leaders
proton stock --page 2    # Global Tech Giants & AI Leaders
proton stock --page 3    # Global Indices, ETFs & Crypto
```

**Dashboard Controls:**
| Key / Command | Description |
|---|---|
| `1` - `20` or `<SYMBOL>` | Deep-dive into stock fundamentals and price chart |
| `next` / `n` | Jump to next page |
| `prev` / `p` | Jump to previous page |
| `page <1-3>` | Switch directly to Page 1, 2, or 3 |
| `refresh` / `r` | Trigger instant price refresh |
| `1d`, `5d`, `1m`, `6m`, `1y` | Inside stock view: switch chart historical timeframe |
| `analyze` | Run Proton AI corporate valuation & growth analysis |
| `ask <question>` | Ask Proton AI questions about the stock's financials |
| `back` / `b` | Return from chart view to market watch table |
| `exit` / `q` | Exit stock tracker |

---

### 11. Host Diagnostics & Resource Telemetry (`proton doctor --sys`)
```bash
# Inspect host hardware, CPU cores, RAM load bar, and disk storage
proton doctor --sys

# Inspect Proton application environment, DB, and AI endpoint status
proton doctor
```

---

### 12. Local Knowledge Base & Hybrid RAG (`proton rag`)
Ingest large programming datasets and documentation into Proton's SQLite vector store:
```bash
# Download and index comprehensive programming knowledge guides
proton rag fetch-knowledge

# Index current workspace source code for retrieval
proton rag index

# Search knowledge base for relevant snippets
proton rag search "binary search tree implementation"

# View total indexed chunks and database path
proton rag status
```

---

### 13. Multi-Provider Connection Management (`proton connection`)
```bash
# Interactive setup wizard
proton connection

# List configured providers
proton connection list

# Test active endpoint latency and auto-discover models
proton connection test

# Switch active connection
proton connection switch <connection-id>
```

---

## 🧠 Recommended Models & Hardware Matrix

Proton connects seamlessly to any model hosted locally (via **LM Studio** or **Ollama**) or over your local network (LAN).

---

### 1. Small Models (1B to 10B Parameters) — *Fast Local Execution*
> **Best for**: Laptops, everyday conversational queries, and fast terminal code generation.

| Model | Parameter Size | Primary Strengths | Recommended Context |
|---|---|---|---|
| **Qwen 2.5 Coder Instruct** | `1.5B` / `7B` | 🥇 **#1 Coding Model for Local Dev**. Superb code generation, refactoring, and function calling. | 32k – 128k tokens |
| **LLaMA 3.2 Instruct** | `1B` / `3B` | Ultra-fast token streaming, low memory usage, sharp conversational reasoning. | 8k – 128k tokens |
| **DeepSeek-R1-Distill-Qwen** | `1.5B` / `7B` / `8B` | Deep step-by-step mathematical reasoning, algorithm planning, and chain-of-thought analysis. | 32k – 64k tokens |
| **Mistral 7B Instruct (v0.3)** | `7B` | General problem-solving, structured JSON outputs, clean instruction-following. | 32k tokens |
| **Gemma 2 Instruct** | `2B` / `9B` | Lightweight Google architecture, clean formatting, accurate summarization. | 8k tokens |

---

### 2. Medium Models (10B to 100B Parameters) — *Coding & Deep Reasoning*
> **Best for**: Dedicated GPU workstations, multi-file code editing, repo-wide search, and complex tool orchestration.

| Model | Parameter Size | Primary Strengths | Recommended Context |
|---|---|---|---|
| **Qwen 2.5 Coder Instruct** | `14B` / `32B` | 🚀 **State-of-the-Art Local Coding Agent**. Outperforms GPT-4o-mini in code synthesis and repo analysis. | 32k – 128k tokens |
| **LLaMA 3.3 Instruct** | `70B` | Enterprise-grade general intelligence, system architecture design, and nuanced reasoning. | 64k – 128k tokens |
| **DeepSeek-R1-Distill-Llama** | `70B` | Elite competitive-level algorithmic reasoning and deep logic analysis. | 64k – 128k tokens |
| **Mistral Small 24B / Codestral** | `22B` / `24B` | Excellent latency-to-quality ratio, native fill-in-the-middle (FIM) code editing. | 32k tokens |
| **Command R+** | `35B` / `104B` | Optimized specifically for RAG document retrieval, citations, and tool routing. | 128k tokens |

---

### 3. Large Models (100B+ Parameters & Frontier MoE) — *Enterprise Agents*
> **Best for**: Multi-GPU clusters, LAN inference servers, or cloud-hosted endpoints requiring frontier intelligence.

| Model | Architecture | Primary Strengths | Recommended Context |
|---|---|---|---|
| **DeepSeek-V3 / DeepSeek-R1** | `671B` (37B active MoE) | 👑 **Frontier Open-Weights Intelligence**. Matches Claude 3.5 Sonnet & GPT-4o across coding, math, and planning. | 64k – 128k tokens |
| **LLaMA 3.1 Instruct** | `405B` Dense | Massive foundation model for synthetic data, full enterprise agent orchestration, and deep domain synthesis. | 128k tokens |
| **Qwen 2.5 Instruct** | `72B` / `110B` | Massive multilingual coding and multi-step complex problem-solving. | 128k tokens |
| **WizardLM-2** | `8x22B` MoE | Highly capable Mixture-of-Experts for software engineering and complex reasoning. | 64k tokens |
| **DBRX Instruct** | `132B` (36B active MoE) | Fast inference speed MoE with high code generation accuracy. | 32k tokens |

---

### ⚡ Hardware Requirements Matrix

| Parameter Scale | Min RAM (CPU Mode) | Recommended GPU (VRAM) | Avg Streaming Speed | Ideal Quantization |
|---|---|---|---|---|
| **1B – 3B** | 8 GB RAM | Integrated GPU or 4 GB VRAM | 30 – 80 tok/s | `Q8_0` or `FP16` |
| **7B – 9B** | 16 GB RAM | 6 GB – 8 GB VRAM (RTX 3060/4060) | 20 – 50 tok/s | `Q4_K_M` or `Q5_K_M` |
| **14B – 32B** | 32 GB RAM | 12 GB – 24 GB VRAM (RTX 3090/4090) | 15 – 35 tok/s | `Q4_K_M` |
| **70B – 72B** | 64 GB RAM | 2x 24 GB VRAM (48GB) or 64GB Mac | 10 – 25 tok/s | `Q4_K_M` |
| **100B+ MoE** | 128 GB RAM | 4x 24 GB VRAM (96GB+) or 128GB Mac | 10 – 20 tok/s | `Q4_K_M` or `IQ4_XS` |

---

## ⌨️ REPL Slash Command Matrix

Inside the interactive `proton >` shell, use built-in slash commands with auto-completion:

| Slash Command | Description |
|---|---|
| `/security [subcmd]` | Security defense verification & workspace audit (`/security test\|audit`) |
| `/benchmark [args]` | Benchmark LLM latency, tok/s, context, tools, RAG, coding, planning |
| `/memory [subcmd]` | Manage categorized memory (`/memory list\|add\|search\|forget\|export\|clear`) |
| `/graph [subcmd]` | Project Knowledge Graph & GraphRAG (`/graph impact\|callers\|tests\|build`) |
| `/inspect [subcmd]` | Deep repo inspection (`/inspect security\|architecture\|dependencies\|tests\|performance`) |
| `/task [subcmd]` | Manage and run persistent development tasks (`/task create\|list\|show\|run\|pause\|resume\|cancel`) |
| `/agent <goal>` | Launch Proton Max-Level Autonomous Agent with 10-stage lifecycle |
| `/stock [SYMBOL]` | Launch live stock market tracker with charts in Rupees (`₹`) |
| `/browser [URL]` | Launch Proton Terminal Web Browser (`/browser --ai_mode`) |
| `/web-search <q>` | Search DuckDuckGo and summarize results with AI |
| `/rag fetch` | Download curated programming knowledge datasets |
| `/rag index` | Index current workspace code for RAG context |
| `/rag search <q>` | Search indexed code and documentation |
| `/doctor` | Run app diagnostics (`/doctor --sys` for host hardware) |
| `/connection` | Open interactive connection manager wizard |
| `/model` | List or switch active model |
| `/review` | Review uncommitted git diffs for bugs and security risks |
| `/diff` | View colorized unstaged git diff |
| `/plan <goal>` | Generate a structured implementation plan |
| `/session list` | View recent conversation sessions |
| `/export` | Export current conversation to Markdown |
| `/clear` | Clear the terminal screen |
| `/help` | Display command help and keyboard shortcuts |
| `/exit` | Exit Proton session (prompts to save named session) |

---

## 🎨 Visual Styling & High-Contrast TUI Engine

Proton implements custom Rich-powered terminal styling tokens:

- **Banner `#` Headings**: Rendered as framed high-contrast banner panels with bold headers.
- **`*` Text Highlighting**: Emphasized words, numbers, and parameters (`**bold**` / `*italic*`) render in bright yellow highlight spans on dark backgrounds.
- **Light-Grey Code Blocks**: Multi-line code snippets stream inside dedicated framed containers with `on grey15` background and syntax labeling.
- **Continuous Sub-Pixel Charts**: Vector braille and box rasterization without asterisks or jagged lines.

---

## 🔒 Enterprise Security & Sandboxing Architecture

- **Execution Sandboxing**: All tool operations are restricted to the active workspace directory.
- **Path Traversal Prevention**: Resolves and canonicalizes all file paths before reading or writing (`FilesystemSandbox`).
- **Secret Redaction**: Automatically scrubs API keys, tokens, and private passwords from logs and prompts (`redact_text`).
- **Approval Policies**:
  - `STRICT` (Default): Prompts for user confirmation before any file modification or shell execution.
  - `BALANCED`: Auto-executes read operations; requires confirmation for write/execute.
  - `PERMISSIVE`: Autonomous execution for unattended workflows.

---

## 📁 Project Directory Topology

```text
Proton/
├── src/
│   └── proton/
│       ├── agent/          # Autonomous agent orchestrator, max agent lifecycle, context assembler, & telemetry
│       ├── benchmark/      # Multi-dimensional LLM benchmark runner (latency, tok/s, context, tools, RAG, coding, planning)
│       ├── browser/        # Terminal browser engine, HTML parser, & DuckDuckGo scraper
│       ├── cli/            # Typer CLI commands (app, security_cmd, benchmark_cmd, agent_cmd, task_cmd, memory_cmd, inspect_cmd, graph_cmd, browser_cmd, stock_cmd, doctor_cmd, rag_cmd)
│       ├── connection/     # Multi-provider connection manager & latency tester
│       ├── core/           # Configuration, types, and database management
│       ├── graph/          # AST code extractor, GraphRAG engine, impact analyzer, and callers map
│       ├── inspect/        # Repository analysis, architecture detector, security auditor, and performance scanner
│       ├── memory/         # Explicit categorized memory store (PROJECT, DECISION, PREFERENCE, FACT, TASK, USER, SESSION)
│       ├── providers/      # LM Studio, Ollama, & OpenAI-compatible providers
│       ├── rag/            # Hybrid vector & BM25 store, chunker, and corpus fetcher
│       ├── security/       # Policy engine, approval manager, sandbox, and automated security verification tester
│       ├── stocks/         # yfinance data service, chart rasterizer, and TUI app
│       ├── tasks/          # Persistent task models, manager, runner, and checkpoints
│       ├── tools/          # File, shell, git, and web search tools
│       └── tui/            # REPL, code highlighter, and autocomplete
├── pyproject.toml          # Package configuration and dependencies
├── .gitignore              # Python, database, and cache ignore rules
├── SECURITY.md             # Security architecture and verification policies
└── README.md               # Project documentation
```

---

## 📜 License

This project is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for details.
