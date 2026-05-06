"""Template support: generate a .env.example from a locked vault."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple


class TemplateError(Exception):
    """Raised when template generation fails."""


_COMMENT_RE = re.compile(r"^\s*#")
_BLANK_RE = re.compile(r"^\s*$")
_KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$")


def parse_env_keys(text: str) -> List[Tuple[str, str]]:
    """Return list of (key, inline_comment) pairs from env text."""
    results: List[Tuple[str, str]] = []
    for line in text.splitlines():
        if _COMMENT_RE.match(line) or _BLANK_RE.match(line):
            continue
        m = _KV_RE.match(line)
        if m:
            key = m.group(1)
            rest = m.group(2).strip()
            # preserve trailing inline comment if present
            comment = ""
            if "  #" in rest:
                comment = rest[rest.index("  #") + 2:].strip()
            results.append((key, comment))
    return results


def generate_template(env_text: str, placeholder: str = "") -> str:
    """Return a .env.example string with values replaced by placeholder."""
    lines: List[str] = []
    for line in env_text.splitlines():
        if _COMMENT_RE.match(line) or _BLANK_RE.match(line):
            lines.append(line)
            continue
        m = _KV_RE.match(line)
        if m:
            key = m.group(1)
            lines.append(f"{key}={placeholder}")
        else:
            lines.append(line)
    return "\n".join(lines) + "\n"


def write_template(env_path: Path, output_path: Path, placeholder: str = "") -> Path:
    """Read *env_path*, generate a template, write to *output_path*."""
    if not env_path.exists():
        raise TemplateError(f"Source file not found: {env_path}")
    text = env_path.read_text(encoding="utf-8")
    template = generate_template(text, placeholder=placeholder)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(template, encoding="utf-8")
    return output_path
