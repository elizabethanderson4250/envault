"""Sanitize .env file values by stripping unsafe characters and normalizing whitespace."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


class SanitizeError(Exception):
    """Raised when sanitization cannot proceed."""


@dataclass
class SanitizeResult:
    original: str
    sanitized: str
    changes: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return self.original != self.sanitized


_UNSAFE_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _sanitize_value(value: str) -> tuple[str, list[str]]:
    """Return (cleaned_value, list_of_change_descriptions)."""
    changes: list[str] = []
    result = value

    # Strip surrounding whitespace
    stripped = result.strip()
    if stripped != result:
        changes.append("stripped surrounding whitespace")
        result = stripped

    # Remove control characters (except \t and \n which may be intentional in quoted values)
    cleaned = _UNSAFE_CTRL.sub("", result)
    if cleaned != result:
        changes.append("removed unsafe control characters")
        result = cleaned

    # Normalize Windows line endings
    normalized = result.replace("\r\n", "\n").replace("\r", "\n")
    if normalized != result:
        changes.append("normalized line endings")
        result = normalized

    return result, changes


def sanitize_line(line: str) -> SanitizeResult:
    """Sanitize a single KEY=VALUE line. Comments and blanks are returned unchanged."""
    stripped = line.rstrip("\n")
    if not stripped or stripped.lstrip().startswith("#"):
        return SanitizeResult(original=line, sanitized=line)

    if "=" not in stripped:
        return SanitizeResult(original=line, sanitized=line)

    key, _, value = stripped.partition("=")
    new_value, changes = _sanitize_value(value)
    sanitized = f"{key}={new_value}"
    if line.endswith("\n"):
        sanitized += "\n"
    return SanitizeResult(original=line, sanitized=sanitized, changes=changes)


def sanitize_env(path: Path) -> list[SanitizeResult]:
    """Read an env file and return per-line SanitizeResult objects."""
    if not path.exists():
        raise SanitizeError(f"File not found: {path}")
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    return [sanitize_line(line) for line in lines]


def apply_sanitize(path: Path) -> list[SanitizeResult]:
    """Sanitize env file in-place. Returns results (only changed lines have changes list)."""
    results = sanitize_env(path)
    new_content = "".join(r.sanitized for r in results)
    path.write_text(new_content, encoding="utf-8")
    return results


def format_sanitize(results: list[SanitizeResult]) -> str:
    """Human-readable summary of sanitization results."""
    changed = [r for r in results if r.changed]
    if not changed:
        return "No issues found — file is clean."
    lines_out = [f"{len(changed)} line(s) sanitized:"]
    for i, r in enumerate(results, start=1):
        if r.changed:
            for c in r.changes:
                lines_out.append(f"  line {i}: {c}")
    return "\n".join(lines_out)
