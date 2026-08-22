# 🛡️ Proton Security Architecture, Policies & Automated Verification

Proton enforces security, data isolation, human control, and **continuous security verification** as foundational platform requirements.

---

## 🔒 Security Principles
1. **Never Silently Execute Side-Effects**: All file modifications, shell executions, and consequential operations require explicit user approval by default.
2. **Workspace Sandboxing**: File operations are confined to the workspace root directory. Any attempt to access files outside (`../../`) triggers a `SecurityError`.
3. **Secret Redaction**: API keys (e.g. `sk-...`, `ghp_...`), Bearer tokens, private keys, and passwords are automatically scrubbed from prompts, logs, telemetry, and error output.
4. **Audit Logging**: All security decisions, tool calls, risk levels, and timestamps are recorded immutably in `~/.proton/audit.db`.
5. **No Hallucinated Execution**: Tools are strictly executed deterministically; the assistant never reports an action as completed unless validated by real tool return values.

---

## 🛡️ Security Verification Battery (`proton security test`)
Rather than relying solely on passive security features, Proton includes an automated defense verification engine that tests all active guardrails against live threat simulations:

```text
┌───────────── 🛡️ Proton Automated Security Defense Verification ─────────────┐
│ Target Workspace: C:\Users\arjun.divekar\Desktop\Proton                     │
│ Defense Checks Passed: 8 / 8   Security Score: 100 / 100                    │
│ Verification Verdict: 🛡️ Enterprise Secure — All Guardrails Verified        │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Threat Vector | Defense Layer | Mitigated Risk |
|---|---|---|
| **Path Traversal** | `FilesystemSandbox.validate_path()` | Blocks directory traversal (`../../etc/passwd`, `..\..\Windows\`) |
| **Workspace Containment** | `FilesystemSandbox.is_safe_relpath()` | Prevents unauthorized workspace breakouts |
| **Command Injection** | `PolicyEngine.evaluate_command()` | Intercepts command chaining (`; rm -rf /`, `&& del /f`, fork bombs) |
| **Dangerous Commands** | `SecurityConfig.blocked_commands` | Intercepts format disk, dd, force push, and table drops |
| **Secret Leakage** | `redact_text()` / `redact_data()` | Cleans API keys, tokens, and passwords before logging |
| **Malicious Tool Args** | `PolicyEngine.get_tool_risk()` | Accurately classifies and gates dangerous tool calls |
| **Prompt Injection** | `ContextAssembler & Policy Evaluator` | Detects adversarial prompt overrides and jailbreaks |
| **Network Boundaries** | `ProviderRegistry Sandboxing` | Restricts outbound LLM inference to user-authorized endpoints |

---

## 🔍 Static Repository Audit (`proton security audit`)
Scans the current workspace for exposed API keys, unsafe file permissions, CVE patterns, and security policy files:

```bash
# Run automated defense test battery
proton security test

# Run static workspace security audit
proton security audit

# View security posture overview
proton security
```

---

## 🚦 Approval Policy Levels
- **Strict (Level 1 - Default)**: Every single tool call and command requires explicit confirmation (`[Allow Once] [Allow Session] [Deny]`).
- **Balanced (Level 2)**: Read-only inspection tools run automatically; file writes and shell commands prompt for approval.
- **Autonomous (Level 4)**: Executes all safe operations within workspace bounds automatically, reserving approvals only for destructive actions.
