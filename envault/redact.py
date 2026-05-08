"""Redact sensitive values from .env content for safe display or logging."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple

# Keys whose values should always be fully redacted
_SENSITIVE_PATTERNS = re.compile(
    r"(secret|password|passwd|token|key|api_key|private|auth|credential|cert|seed|salt)",
    re.IGNORECASE,
)

_PLACEHOLDER = "***REDACTED***"


@dataclass
class RedactedLine:
    original: str
    redacted: str
    was_redacted: bool


def _is_sensitive_key(key: str) -> bool:
    """Return True if the key name looks sensitive."""
    return bool(_SENSITIVE_PATTERNS.search(key))


def _mask_value(value: str, show_chars: int = 0) -> str:
    """Mask a value, optionally revealing the first N characters."""
    if not value:
        return value
    if show_chars <= 0 or show_chars >= len(value):
        return _PLACEHOLDER
    return value[:show_chars] + "..." + _PLACEHOLDER


def redact_line(line: str, show_chars: int = 0) -> RedactedLine:
    """Redact a single .env line if the key is sensitive."""
    stripped = line.rstrip("\n")
    if stripped.startswith("#") or "=" not in stripped or not stripped.strip():
        return RedactedLine(original=line, redacted=line, was_redacted=False)

    key, _, value = stripped.partition("=")
    key = key.strip()
    value = value.strip().strip('"').strip("'")

    if _is_sensitive_key(key):
        masked = _mask_value(value, show_chars)
        redacted_line = f"{key}={masked}"
        return RedactedLine(original=line, redacted=redacted_line, was_redacted=True)

    return RedactedLine(original=line, redacted=stripped, was_redacted=False)


def redact_env(content: str, show_chars: int = 0) -> Tuple[str, List[str]]:
    """Redact all sensitive values in .env content.

    Returns:
        (redacted_content, list_of_redacted_keys)
    """
    lines = content.splitlines(keepends=True)
    result_lines: List[str] = []
    redacted_keys: List[str] = []

    for line in lines:
        rl = redact_line(line, show_chars=show_chars)
        result_lines.append(rl.redacted)
        if rl.was_redacted:
            key = line.partition("=")[0].strip()
            redacted_keys.append(key)

    return "\n".join(result_lines), redacted_keys


def format_redact_summary(redacted_keys: List[str]) -> str:
    """Return a human-readable summary of what was redacted."""
    if not redacted_keys:
        return "No sensitive keys detected."
    keys_str = ", ".join(redacted_keys)
    return f"Redacted {len(redacted_keys)} sensitive key(s): {keys_str}"
