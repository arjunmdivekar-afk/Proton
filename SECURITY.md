# Proton Security Architecture & Policies

Proton enforces security, data isolation, and human control as foundational platform requirements.

## Security Principles
1. **Never Silently Execute Side-Effects**: All file modifications, shell executions, and consequential operations require explicit user approval by default.
2. **Workspace Sandboxing**: File operations are confined to the workspace root directory. Any attempt to access files outside (`../../`) triggers a `SecurityError`.
3. **Secret Redaction**: API keys (e.g. `sk-...`, `ghp_...`), Bearer tokens, private keys, and passwords are automatically scrubbed from prompts, logs, telemetry, and error output.
4. **Audit Logging**: All security decisions, tool calls, risk levels, and timestamps are recorded immutably in `~/.proton/audit.db`.
5. **No Hallucinated Execution**: Tools are strictly executed deterministically; the assistant never reports an action as completed unless validated by real tool return values.

## Approval Policy Levels
- **Strict (Level 1 - Default)**: Every single tool call and command requires explicit confirmation (`[Allow Once] [Allow Session] [Deny]`).
- **Balanced (Level 2)**: Read-only inspection tools run automatically; file writes and shell commands prompt for approval.
- **Autonomous (Level 4)**: Executes all safe operations within workspace bounds automatically, reserving approvals only for destructive actions.
