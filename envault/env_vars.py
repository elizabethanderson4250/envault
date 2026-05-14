"""Utilities for listing, getting, and setting individual env var entries."""
from __future__ import annotations

from pathlib import Path
from typing import Optional


class EnvVarError(Exception):
    """Raised when an env var operation fails."""


def _is_comment_or_blank(line: str) -> bool:
    stripped = line.strip()
    return stripped == "" or stripped.startswith("#")


def _key_of(line: str) -> Optional[str]:
    if _is_comment_or_blank(line) or "=" not in line:
        return None
    return line.split("=", 1)[0].strip()


def list_keys(env_path: Path) -> list[str]:
    """Return all variable names defined in an env file."""
    if not env_path.exists():
        raise EnvVarError(f"File not found: {env_path}")
    keys = []
    for line in env_path.read_text().splitlines():
        key = _key_of(line)
        if key:
            keys.append(key)
    return keys


def get_value(env_path: Path, key: str) -> str:
    """Return the value for *key* in the env file.

    Raises EnvVarError if the file is missing or the key is not found.
    """
    if not env_path.exists():
        raise EnvVarError(f"File not found: {env_path}")
    for line in env_path.read_text().splitlines():
        if _key_of(line) == key:
            value = line.split("=", 1)[1].strip()
            # Strip surrounding quotes
            if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
                value = value[1:-1]
            return value
    raise EnvVarError(f"Key not found: {key}")


def set_value(env_path: Path, key: str, value: str) -> bool:
    """Set *key* to *value* in the env file, adding it if absent.

    Returns True if an existing key was updated, False if it was added.
    """
    if not env_path.exists():
        raise EnvVarError(f"File not found: {env_path}")
    lines = env_path.read_text().splitlines(keepends=True)
    updated = False
    new_lines = []
    for line in lines:
        if _key_of(line) == key:
            new_lines.append(f"{key}={value}\n")
            updated = True
        else:
            new_lines.append(line)
    if not updated:
        # Ensure file ends with newline before appending
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"
        new_lines.append(f"{key}={value}\n")
    env_path.write_text("".join(new_lines))
    return updated


def delete_key(env_path: Path, key: str) -> None:
    """Remove *key* from the env file.

    Raises EnvVarError if the file is missing or the key is not found.
    """
    if not env_path.exists():
        raise EnvVarError(f"File not found: {env_path}")
    lines = env_path.read_text().splitlines(keepends=True)
    new_lines = [line for line in lines if _key_of(line) != key]
    if len(new_lines) == len(lines):
        raise EnvVarError(f"Key not found: {key}")
    env_path.write_text("".join(new_lines))
