# ⚛️ Proton — Enterprise AI CLI Assistant & Agent Platform `v1.4.0`

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg)](https://github.com/arjunmdivekar-afk/Proton)
[![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

> **Proton** is a high-performance, provider-neutral AI CLI assistant, autonomous software engineering agent, terminal web browser, and market intelligence platform designed for developers, DevOps engineers, and researchers operating directly from the terminal.

---

## 📑 Table of Contents
- [✨ Key Features](#-key-features)
- [📦 Quick Installation](#-quick-installation)
- [🚀 Quick Start](#-quick-start)
- [💻 CLI Command Reference](#-cli-command-reference)
  - [1. Max-Level Autonomous Agent (`proton agent`)](#1-max-level-autonomous-agent-proton-agent)
  - [2. Interactive AI Assistant (`proton`)](#2-interactive-ai-assistant-proton)
  - [3. Terminal Web Browser (`proton browser`)](#3-terminal-web-browser-proton-browser)
  - [4. Live Stock Market Tracker (`proton stock`)](#4-live-stock-market-tracker-proton-stock)
  - [5. Host System Diagnostics (`proton doctor --sys`)](#5-host-system-diagnostics-proton-doctor---sys)
  - [6. Knowledge Base & Hybrid RAG (`proton rag`)](#6-knowledge-base--hybrid-rag-proton-rag)
  - [7. Connection Manager (`proton connection`)](#7-connection-manager-proton-connection)
- [🧠 Recommended Models & Hardware Requirements](#-recommended-models--hardware-requirements)
  - [1. Small Models (1B to 10B)](#1-small-models-1b-to-10b-parameters--fast-local-execution)
  - [2. Medium Models (10B to 100B)](#2-medium-models-10b-to-100b-parameters--coding--deep-reasoning)
  - [3. Large Models (100B+)](#3-large-models-100b-parameters--frontier-moe--enterprise-agents)
  - [⚡ Hardware Requirements Matrix](#-hardware-requirements-matrix)
- [⌨️ REPL Slash Commands](#️-repl-slash-commands)
- [🎨 Visual Styling & Markdown Formatting](#-visual-styling--markdown-formatting)
- [🔒 Security & Approvals](#-security--approvals)
- [📁 Project Architecture](#-project-architecture)
- [📜 License](#-license)

---

## ✨ Key Features

- **🤖 Max-Level Autonomous Agent**: 10-stage autonomous lifecycle (`Understand Task ➔ Inspect Repo ➔ Create Plan ➔ Ask Approval ➔ Use Tools ➔ Modify Files ➔ Run Tests ➔ Review Changes ➔ Fix Failures ➔ Generate Report`) with self-healing and automatic code persistence.
- **🌐 Provider & Model Neutral**: First-class support for **LM Studio** (local and LAN IP `http://192.168.x.x:1234`), **Ollama**, and any OpenAI-compatible inference server.
- **⚡ Interactive Stream-First TUI REPL**: Live token streaming, light-grey code block highlights, large `#` heading panels, and `*` text highlighting.
- **🌍 Proton Terminal Web Browser**: Keyboard-first browser with live DuckDuckGo web search, numbered interactive links `[1-50]`, multi-hop page navigation, and embedded **Proton AI Copilot** (`/browser --ai_mode`).
- **📈 Live Stock Market Tracker (`yfinance`)**: Real-time stock dashboard in **Indian Rupees (`₹`)** with 10-minute auto-refresh, 20 stocks per page across Indian NSE/BSE & Global markets, high-resolution continuous vector price charts, and **Proton AI Stock Analyst**.
- **🖥️ Host System & Hardware Diagnostics**: `proton doctor --sys` inspects CPU cores, live RAM usage bar, disk partitions, uptime, and network interfaces.
- **🧠 Local Hybrid Vector & BM25 RAG**: In-process parent-child chunking with SQLite vector indexing (`~/.proton/knowledge/`) and dynamic code retrieval (`proton rag fetch-knowledge`).
- **🛡️ Strict Human-in-the-Loop Security**: Path traversal prevention, secret redaction, granular tool execution policies, and audit logging.

---

## 📦 Quick Installation

### 1. Clone the Repository
```bash
git clone https://github.com/arjunmdivekar-afk/Proton.git
cd Proton
```

### 2. Install Dependencies in Editable Mode
```bash
pip install -e .
```

### 3. Verify Installation
```bash
proton --version
# Output: Proton version 1.4.0
```

---

## 🚀 Quick Start

```bash
# 1. Configure and test your AI connection (LM Studio / Ollama)
proton connection

# 2. Launch interactive Autonomous Agent on a software task
proton agent "create responsive navigation header with tests"

# 3. Launch the interactive AI Assistant REPL
proton

# 4. Launch Proton Terminal Web Browser
proton browser "fastapi tutorial"

# 5. Launch Live Stock Market Tracker in Indian Rupees (₹)
proton stock

# 6. Check host machine hardware & RAM status
proton doctor --sys
```

---

## 💻 CLI Command Reference

### 1. Max-Level Autonomous Agent (`proton agent`)
Execute end-to-end software engineering tasks with a full **10-stage autonomous lifecycle**:

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

### 2. Interactive AI Assistant (`proton`)
Launch the interactive terminal session with live token streaming and memory:
```bash
# Launch interactive REPL
proton

# Run non-interactive query
proton ask "Explain the architecture of this project"

# Output machine-readable JSON
proton ask "Generate quicksort in python" --json
```

---

### 3. Terminal Web Browser (`proton browser`)
Browse the internet, search via DuckDuckGo, open numbered links, and summarize pages using AI:
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

### 4. Live Stock Market Tracker (`proton stock`)
Live market intelligence in **Indian Rupees (`₹`)** with 10-minute auto-refresh, 20 assets per page, and continuous price charts:
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

**Stock Dashboard Controls:**
| Key / Command | Description |
|---|---|
| `1` - `20` or `<SYMBOL>` | Deep-dive into stock fundamentals and price chart |
| `next` / `n` | Jump to next page |
| `prev` / `p` | Jump to previous page |
| `page <1-3>` | Switch directly to Page 1, 2, or 3 |
| `refresh` / `r` | Trigger instant price refresh |
| `1d`, `5d`, `1m`, `6m`, `1y` | Inside stock view: switch chart historical timeframe |
| `analyze` | Run Proton AI corporate metrics, valuation & growth analysis |
| `ask <question>` | Ask Proton AI questions about the stock's financials |
| `back` / `b` | Return from chart view to market watch table |
| `exit` / `q` | Exit stock tracker |

---

### 5. Host System Diagnostics (`proton doctor --sys`)
```bash
# Inspect host machine hardware, CPU cores, RAM load bar, and disk storage
proton doctor --sys

# Inspect Proton application environment, DB, and AI endpoint status
proton doctor
```

---

### 6. Knowledge Base & Hybrid RAG (`proton rag`)
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

### 7. Connection Manager (`proton connection`)
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

## 🧠 Recommended Models & Hardware Requirements

Proton connects seamlessly to any model hosted locally (via **LM Studio** or **Ollama**) or over your local network (LAN). Below are our curated recommendations categorized by model parameter scale:

---

### 1. Small Models (1B to 10B Parameters) — *Fast Local Execution*
> **Best for**: Laptops, lightweight PCs, everyday conversational queries, and fast terminal code generation.

| Model | Parameter Size | Primary Strengths | Recommended Context |
|---|---|---|---|
| **Qwen 2.5 Coder Instruct** | `1.5B` / `7B` | 🥇 **#1 Coding Model for Local Dev**. Superb code generation, refactoring, and function calling. | 32k – 128k tokens |
| **LLaMA 3.2 Instruct** | `1B` / `3B` | Ultra-fast token streaming, low memory usage, sharp conversational reasoning. | 8k – 128k tokens |
| **DeepSeek-R1-Distill-Qwen** | `1.5B` / `7B` / `8B` | Deep step-by-step mathematical reasoning, algorithm planning, and chain-of-thought analysis. | 32k – 64k tokens |
| **Mistral 7B Instruct (v0.3)** | `7B` | General problem-solving, structured JSON outputs, clean instruction-following. | 32k tokens |
| **Gemma 2 Instruct** | `2B` / `9B` | Lightweight Google architecture, clean formatting, accurate summarization. | 8k tokens |

**💻 Hardware Requirements (Small Models):**
- **RAM**: 8 GB – 16 GB System RAM (CPU only) or 4 GB – 8 GB VRAM.
- **GPU**: Integrated GPU (Intel Iris Xe / AMD Radeon) or NVIDIA GTX 1650 / RTX 3050 / Apple M1/M2/M3 (8GB+).
- **Disk Space**: ~2 GB – 6 GB per GGUF model (`Q4_K_M` quantization).

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

**💻 Hardware Requirements (Medium Models):**
- **RAM / VRAM**: 32 GB – 64 GB System RAM (or 16 GB – 48 GB VRAM).
- **GPU**: 1x or 2x NVIDIA RTX 3090 / 4090 (24GB VRAM) / RTX 4080 (16GB) / Apple M2/M3/M4 Pro or Max (36GB – 64GB Unified Memory).
- **Disk Space**: ~10 GB – 45 GB per GGUF model (`Q4_K_M` / `Q5_K_M`).

---

### 3. Large Models (100B+ Parameters & Frontier MoE) — *Enterprise Agents*
> **Best for**: Dedicated multi-GPU clusters, LAN inference servers, or cloud-hosted endpoints requiring frontier intelligence.

| Model | Architecture | Primary Strengths | Recommended Context |
|---|---|---|---|
| **DeepSeek-V3 / DeepSeek-R1** | `671B` (37B active MoE) | 👑 **Frontier Open-Weights Intelligence**. Matches Claude 3.5 Sonnet & GPT-4o across coding, math, and planning. | 64k – 128k tokens |
| **LLaMA 3.1 Instruct** | `405B` Dense | Massive foundation model for synthetic data, full enterprise agent orchestration, and deep domain synthesis. | 128k tokens |
| **Qwen 2.5 Instruct** | `72B` / `110B` | Massive multilingual coding and multi-step complex problem-solving. | 128k tokens |
| **WizardLM-2** | `8x22B` MoE | Highly capable Mixture-of-Experts for software engineering and complex reasoning. | 64k tokens |
| **DBRX Instruct** | `132B` (36B active MoE) | Fast inference speed MoE with high code generation accuracy. | 32k tokens |

**💻 Hardware Requirements (Large Models):**
- **RAM / VRAM**: 128 GB – 256 GB+ Unified Memory or Multi-GPU Clusters (4x–8x RTX 3090/4090 24GB, 2x–4x NVIDIA A100/H100 80GB, or Apple M2/M3/M4 Ultra with 128GB–192GB Unified Memory).
- **Alternatively**: Connect Proton to a LAN server or cloud API endpoint running these models using `proton connection`.
- **Disk Space**: ~70 GB – 250 GB+ NVMe SSD.

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

## ⌨️ REPL Slash Commands

Inside the interactive `proton >` shell, you can use built-in slash commands with auto-completion:

| Slash Command | Description |
|---|---|
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
| `/memory` | Inspect persistent project memory records |
| `/session list` | View recent conversation sessions |
| `/export` | Export current conversation to Markdown |
| `/clear` | Clear the terminal screen |
| `/help` | Display command help and keyboard shortcuts |
| `/exit` | Exit Proton session |

---

## 🎨 Visual Styling & Markdown Formatting

Proton features a custom terminal styling engine:

- **Large `#` Headings**: Rendered as distinct 3-line tall framed banner panels with bold contrast and dividing rules.
- **`*` Text Highlighting**: Emphasized words, numbers, and parameters (`**bold**` / `*italic*`) render in bright yellow highlight spans on dark backgrounds.
- **Light-Grey Code Blocks**: Multi-line code snippets stream inside dedicated framed containers with `on grey15` background and syntax labeling.
- **Clean Continuous Charts**: Stock price trends use a 2x4 sub-pixel vector rasterizer without asterisks or slashes.

---

## 🔒 Security & Approvals

Proton includes an enterprise-grade security layer:
- **Execution Sandboxing**: All tool actions are restricted to the active workspace directory.
- **Path Traversal Prevention**: Resolves and canonicalizes all file paths before reading or writing.
- **Secret Redaction**: Automatically scrubs API keys, tokens, and private passwords from logs and prompts.
- **Approval Policies**:
  - `STRICT`: Prompts for user confirmation before any file modification or shell execution.
  - `BALANCED`: Auto-executes read operations; requires confirmation for write/execute.
  - `PERMISSIVE`: Autonomous execution for unattended workflows.

---

## 📁 Project Architecture

```text
Proton/
├── src/
│   └── proton/
│       ├── agent/          # Autonomous agent orchestrator, max agent lifecycle, context assembler, & telemetry
│       ├── browser/        # Terminal browser engine, HTML parser, & DuckDuckGo scraper
│       ├── cli/            # Typer CLI commands (app, agent_cmd, browser_cmd, stock_cmd, doctor_cmd, rag_cmd)
│       ├── connection/     # Multi-provider connection manager & latency tester
│       ├── core/           # Configuration, types, and database management
│       ├── memory/         # Persistent memory and session management
│       ├── providers/      # LM Studio, Ollama, & OpenAI-compatible providers
│       ├── rag/            # Hybrid vector & BM25 store, chunker, and corpus fetcher
│       ├── security/       # Policy engine, approval manager, and sandbox
│       ├── stocks/         # yfinance data service, chart rasterizer, and TUI app
│       ├── tools/          # File, shell, git, and web search tools
│       └── tui/            # REPL, code highlighter, and autocomplete
├── pyproject.toml          # Package configuration and dependencies
├── .gitignore              # Python, database, and cache ignore rules
└── README.md               # Project documentation
```

---

## 📜 License

This project is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for details.
