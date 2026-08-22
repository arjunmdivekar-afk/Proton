# ⚛️ Proton — Enterprise AI CLI Assistant & Agent Platform `v1.4.0`

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg)](https://github.com/arjunmdivekar-afk/Proton)
[![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

> **Proton** is a high-performance, provider-neutral AI CLI assistant, terminal web browser, and market intelligence platform designed for developers, DevOps engineers, and researchers operating directly from the terminal.

---

## 📑 Table of Contents
- [✨ Key Features](#-key-features)
- [📦 Quick Installation](#-quick-installation)
- [🚀 Quick Start](#-quick-start)
- [💻 CLI Command Reference](#-cli-command-reference)
  - [1. Interactive AI Assistant (`proton`)](#1-interactive-ai-assistant-proton)
  - [2. Terminal Web Browser (`proton browser`)](#2-terminal-web-browser-proton-browser)
  - [3. Live Stock Market Tracker (`proton stock`)](#3-live-stock-market-tracker-proton-stock)
  - [4. Host System Diagnostics (`proton doctor --sys`)](#4-host-system-diagnostics-proton-doctor---sys)
  - [5. Knowledge Base & Hybrid RAG (`proton rag`)](#5-knowledge-base--hybrid-rag-proton-rag)
  - [6. Connection Manager (`proton connection`)](#6-connection-manager-proton-connection)
- [⌨️ REPL Slash Commands](#️-repl-slash-commands)
- [🎨 Visual Styling & Markdown Formatting](#-visual-styling--markdown-formatting)
- [🔒 Security & Approvals](#-security--approvals)
- [📁 Project Architecture](#-project-architecture)
- [📜 License](#-license)

---

## ✨ Key Features

- **🌐 Provider & Model Neutral**: First-class support for **LM Studio** (local and LAN IP `http://192.168.x.x:1234`), **Ollama**, and any OpenAI-compatible inference server.
- **⚡ Interactive Stream-First TUI REPL**: Live token streaming, light-grey code block highlights, large `#` heading panels, and `*` text highlighting.
- **🌍 Proton Terminal Web Browser**: Keyboard-first browser with live DuckDuckGo web search, numbered interactive links `[1-20]`, multi-hop page navigation, and embedded **Proton AI Copilot** (`/browser --ai_mode`).
- **📈 Live Stock Market Tracker (`yfinance`)**: Real-time stock dashboard in **Indian Rupees (`₹`)** with 10-minute auto-refresh, 20 stocks per page across Indian NSE/BSE & Global markets, high-resolution continuous vector price charts, and **Proton AI Stock Analyst**.
- **🖥️ Host System & Hardware Diagnostics**: `proton doctor --sys` inspects CPU cores, live RAM usage bar, disk partitions, uptime, and network interfaces.
- **🧠 Local Hybrid Vector & BM25 RAG**: In-process parent-child chunking with SQLite vector indexing (`~/.proton/knowledge/`) and dynamic code retrieval.
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

# 2. Launch the interactive AI Assistant REPL
proton

# 3. Launch Proton Terminal Web Browser
proton browser "react 19 release notes"

# 4. Launch Live Stock Market Tracker in Indian Rupees (₹)
proton stock

# 5. Check host machine hardware & RAM status
proton doctor --sys
```

---

## 💻 CLI Command Reference

### 1. Interactive AI Assistant (`proton`)
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

### 2. Terminal Web Browser (`proton browser`)
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

### 3. Live Stock Market Tracker (`proton stock`)
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

### 4. Host System Diagnostics (`proton doctor --sys`)
```bash
# Inspect host machine hardware, CPU cores, RAM load bar, and disk storage
proton doctor --sys

# Inspect Proton application environment, DB, and AI endpoint status
proton doctor
```

---

### 5. Knowledge Base & Hybrid RAG (`proton rag`)
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

### 6. Connection Manager (`proton connection`)
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

## ⌨️ REPL Slash Commands

Inside the interactive `proton >` shell, you can use built-in slash commands with auto-completion:

| Slash Command | Description |
|---|---|
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
│       ├── agent/          # Agent orchestration engine, context assembler, & telemetry
│       ├── browser/        # Terminal browser engine, HTML parser, & DuckDuckGo scraper
│       ├── cli/            # Typer CLI commands (app, browser_cmd, stock_cmd, doctor_cmd)
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
