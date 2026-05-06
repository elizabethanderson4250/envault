"""Import .env values from an existing plaintext file into the vault."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Tuple


class ImportError(Exception):  # noqa: A001
    """Raised when an import operation fails."""


def parse_env_file(path: Path) -> Dict[str, str]:
    """Parse a .env file and return a dict of key-value pairs."""
    if not path.exists():
        raise ImportError(f"File not found: {path}")

    pairs: Dict[str, str] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            pairs[key] = value
    return pairs


def merge_env(
    existing: Dict[str, str],
    incoming: Dict[str, str],
    overwrite: bool = False,
) -> Tuple[Dict[str, str], List[str], List[str]]:
    """Merge *incoming* into *existing*.

    Returns (merged, added_keys, skipped_keys).
    """
    merged = dict(existing)
    added: List[str] = []
    skipped: List[str] = []

    for key, value in incoming.items():
        if key in merged and not overwrite:
            skipped.append(key)
        else:
            merged[key] = value
            added.append(key)

    return merged, added, skipped


def write_env_file(path: Path, pairs: Dict[str, str]) -> None:
    """Write *pairs* to a .env file, one KEY=VALUE per line."""
    lines = [f"{k}={v}\n" for k, v in pairs.items()]
    path.write_text("".join(lines), encoding="utf-8")
