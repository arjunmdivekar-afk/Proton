"""Secret detection and redaction engine for Proton."""

import re
from typing import Any, Dict, List, Union

# Common credential patterns
PATTERNS = [
    # Generic API Keys / Tokens
    re.compile(r'(?i)(api[_-]?key|secret|token|password|passwd|auth)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{12,})["\']?'),
    # Bearer tokens
    re.compile(r'(?i)bearer\s+([a-zA-Z0-9_\-\.]{20,})'),
    # OpenAI format
    re.compile(r'sk-[a-zA-Z0-9]{20,}'),
    # Hugging Face access tokens
    re.compile(r'hf_[a-zA-Z0-9]{20,}'),
    # GitHub personal access tokens
    re.compile(r'gh[pousr]_[a-zA-Z0-9]{36,}'),
    # AWS access key / secret
    re.compile(r'AKIA[0-9A-Z]{16}'),
    # RSA / Private Key headers
    re.compile(r'-----BEGIN [A-Z ]+ PRIVATE KEY-----[^-]+-----END [A-Z ]+ PRIVATE KEY-----', re.DOTALL),
]


def redact_text(text: str) -> str:
    """Scrub sensitive credentials and secrets from text."""
    if not text or not isinstance(text, str):
        return text

    redacted = text
    for pattern in PATTERNS:
        def _repl(match: re.Match) -> str:
            val = match.group(0)
            if len(match.groups()) >= 2:
                # Replace the secret capturing group
                prefix = match.group(1)
                return f"{prefix}=***REDACTED***"
            elif len(match.groups()) == 1:
                return f"***REDACTED***"
            return "***REDACTED_SECRET***"

        redacted = pattern.sub(_repl, redacted)

    return redacted


def redact_data(data: Any) -> Any:
    """Recursively scrub secrets from dicts, lists, and strings."""
    if isinstance(data, str):
        return redact_text(data)
    elif isinstance(data, dict):
        new_dict: Dict[str, Any] = {}
        for k, v in data.items():
            if any(s in k.lower() for s in ("password", "secret", "token", "api_key", "auth_header")):
                new_dict[k] = "***REDACTED***"
            else:
                new_dict[k] = redact_data(v)
        return new_dict
    elif isinstance(data, list):
        return [redact_data(item) for item in data]
    return data
