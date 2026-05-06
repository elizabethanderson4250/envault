"""Export decrypted .env content to various formats (dotenv, JSON, shell export)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple


class ExportError(Exception):
    """Raised when export fails."""


SUPPORTED_FORMATS = ("dotenv", "json", "shell")


def parse_env_pairs(text: str) -> List[Tuple[str, str]]:
    """Parse env text into ordered list of (key, value) tuples, preserving comments."""
    pairs: List[Tuple[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            pairs.append((key, value))
    return pairs


def export_dotenv(pairs: List[Tuple[str, str]]) -> str:
    """Render pairs as standard dotenv format."""
    return "\n".join(f'{k}="{v}"' for k, v in pairs) + "\n"


def export_json(pairs: List[Tuple[str, str]]) -> str:
    """Render pairs as a JSON object."""
    return json.dumps(dict(pairs), indent=2) + "\n"


def export_shell(pairs: List[Tuple[str, str]]) -> str:
    """Render pairs as shell export statements."""
    return "\n".join(f'export {k}="{v}"' for k, v in pairs) + "\n"


_RENDERERS = {
    "dotenv": export_dotenv,
    "json": export_json,
    "shell": export_shell,
}


def export_env(env_text: str, fmt: str) -> str:
    """Convert env text to the requested format string.

    Args:
        env_text: Raw contents of a decrypted .env file.
        fmt: One of 'dotenv', 'json', 'shell'.

    Returns:
        Formatted string.

    Raises:
        ExportError: If fmt is not supported.
    """
    if fmt not in _RENDERERS:
        raise ExportError(
            f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )
    pairs = parse_env_pairs(env_text)
    return _RENDERERS[fmt](pairs)


def write_export(content: str, output: Path) -> None:
    """Write exported content to a file."""
    output.write_text(content, encoding="utf-8")
