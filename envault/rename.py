"""Rename a key inside a decrypted .env file in-place."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


class RenameError(Exception):
    """Raised when a rename operation fails."""


def rename_key(
    env_path: Path,
    old_key: str,
    new_key: str,
    *,
    overwrite: bool = False,
) -> int:
    """Rename *old_key* to *new_key* in the .env file at *env_path*.

    Returns the line number (1-based) where the rename occurred.
    Raises RenameError if the file is missing, the key is not found,
    or *new_key* already exists and *overwrite* is False.
    """
    if not env_path.exists():
        raise RenameError(f"File not found: {env_path}")

    if not _is_valid_key(old_key):
        raise RenameError(f"Invalid key name: {old_key!r}")
    if not _is_valid_key(new_key):
        raise RenameError(f"Invalid key name: {new_key!r}")

    lines = env_path.read_text(encoding="utf-8").splitlines(keepends=True)

    old_lineno: Optional[int] = None
    new_exists_lineno: Optional[int] = None

    for i, line in enumerate(lines, start=1):
        key = _key_of_line(line)
        if key == old_key:
            old_lineno = i
        elif key == new_key:
            new_exists_lineno = i

    if old_lineno is None:
        raise RenameError(f"Key {old_key!r} not found in {env_path}")

    if new_exists_lineno is not None and not overwrite:
        raise RenameError(
            f"Key {new_key!r} already exists at line {new_exists_lineno}; "
            "pass overwrite=True to replace it"
        )

    updated: list[str] = []
    for line in lines:
        key = _key_of_line(line)
        if key == new_key and new_exists_lineno is not None and overwrite:
            # Drop the old occurrence of new_key when overwriting
            continue
        if key == old_key:
            line = re.sub(r"^[^=]+", new_key, line, count=1)
        updated.append(line)

    env_path.write_text("".join(updated), encoding="utf-8")
    return old_lineno


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _is_valid_key(name: str) -> bool:
    return bool(_KEY_RE.match(name))


def _key_of_line(line: str) -> Optional[str]:
    """Return the key part of an assignment line, or None."""
    stripped = line.strip()
    if stripped.startswith("#") or "=" not in stripped:
        return None
    key = stripped.split("=", 1)[0].strip()
    return key if _is_valid_key(key) else None
