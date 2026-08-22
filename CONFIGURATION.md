# Proton Configuration Guide

Proton supports a hierarchical configuration model:
1. Built-in defaults
2. User global configuration (`~/.proton/config.yaml`)
3. Workspace project configuration (`./.proton/config.yaml`)
4. Environment variables (`PROTON_HOME`, `PROTON_ACTIVE_CONNECTION`, `PROTON_ACTIVE_MODEL`)

## Sample `~/.proton/config.yaml`

```yaml
active_connection: default-lmstudio
active_model: null

security:
  approval_policy: strict
  sandbox_workspace_only: true
  allowed_commands:
    - git
    - python
    - pytest
    - npm
    - cargo
  redact_secrets: true

agent:
  max_steps: 30
  max_tool_calls: 50
  timeout_seconds: 300
  autonomy_level: 1

rag:
  enabled: true
  chunk_size: 800
  chunk_overlap: 100
  top_k: 5
  min_similarity: 0.2
  hybrid_search: true

ui:
  theme: default
  streaming: true
  show_token_counter: true
  show_latency: true
```

## AI Connection Management (`~/.proton/connections.yaml`)

Configure multiple local or remote LAN AI endpoints:

```yaml
default-lmstudio:
  name: Local LM Studio
  provider: lmstudio
  host: 127.0.0.1
  port: 1234
  protocol: http
  base_path: /v1
  enabled: true

office-lm-studio-pc:
  name: Office LM Studio PC
  provider: lmstudio
  host: 192.168.1.50
  port: 1234
  protocol: http
  base_path: /v1
  enabled: true

default-ollama:
  name: Local Ollama
  provider: ollama
  host: 127.0.0.1
  port: 11434
  protocol: http
  base_path: /v1
  enabled: true
```

## CLI Configuration Commands
```bash
# Manage connections
proton connection
proton connection list
proton connection add lmstudio --host 192.168.1.50 --port 1234
proton connection use office-lm-studio-pc
proton connection test

# Run environment health check
proton doctor
```
