# Proton — Enterprise AI CLI Assistant

Proton is a production-quality, enterprise-grade AI CLI assistant and agent platform operating from the terminal.

## Key Features
- **Provider & Model Neutral**: Seamless integration with LM Studio (local & LAN IP e.g. `192.168.1.50:1234`), Ollama, and OpenAI-compatible inference servers.
- **Connection Manager**: `proton connection` interactive wizard and CLI to configure, probe, latency test, and auto-discover models.
- **Interactive TUI REPL**: Stream-first rich terminal with live markdown streaming, command autocompletion, diff viewer, and inline approvals.
- **Coding & DevOps Agent**: Code search, unified diff patch engine, file modifications, git automation, test runners.
- **Local-First Hybrid RAG**: In-process hybrid vector & BM25 retrieval with parent-child chunking and real verifiable citations.
- **DuckDuckGo Web Search**: Live internet lookup via `/web-search <query>` or autonomous `duckduckgo_search` & `fetch_web_page` tools with citations.
- **Strict Security & Approvals**: Human-in-the-loop approval workflows, path traversal prevention, secret redaction, and audit logging.

## Installation
```bash
pip install -e .
```

## Quick Start
```bash
# Launch interactive REPL
proton

# Manage AI Connections
proton connection

# Non-interactive queries
proton ask "Explain this project structure"
proton ask "Generate quicksort in python" --json

# Launch Proton Terminal Web Browser with link navigation
proton browser "react 19 release notes"
proton browser https://react.dev

# Launch Proton Browser in AI Copilot Mode
proton browser --ai_mode
proton browser "python tutorial" --ai_mode

# Run application and AI endpoint diagnostics
proton doctor

# Launch Live Stock Market Tracker (2s auto-refresh, 20 stocks/page)
proton stock

# Inspect specific stock with deep-dive fundamentals and ASCII price chart
proton stock AAPL
proton stock NVDA
```
