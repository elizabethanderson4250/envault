"""Diff utilities for comparing .env file versions stored in the vault."""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class EnvDiff:
    """Result of comparing two .env snapshots."""

    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    unchanged: Dict[str, str] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def parse_env(text: str) -> Dict[str, str]:
    """Parse a .env file text into a key->value mapping.

    Lines starting with '#' or that are blank are ignored.
    Values may optionally be quoted with single or double quotes.
    """
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        result[key] = value
    return result


def diff_env(old_text: str, new_text: str) -> EnvDiff:
    """Compare two .env file contents and return an EnvDiff."""
    old = parse_env(old_text)
    new = parse_env(new_text)

    result = EnvDiff()
    all_keys = set(old) | set(new)

    for key in sorted(all_keys):
        in_old = key in old
        in_new = key in new
        if in_old and in_new:
            if old[key] != new[key]:
                result.changed[key] = (old[key], new[key])
            else:
                result.unchanged[key] = old[key]
        elif in_new:
            result.added[key] = new[key]
        else:
            result.removed[key] = old[key]

    return result


def format_diff(diff: EnvDiff, mask_values: bool = True) -> List[str]:
    """Return a human-readable list of diff lines.

    If *mask_values* is True, secret values are replaced with '***'.
    """
    lines: List[str] = []
    mask = lambda v: "***" if mask_values else v  # noqa: E731

    for key, value in sorted(diff.added.items()):
        lines.append(f"+ {key}={mask(value)}")
    for key, value in sorted(diff.removed.items()):
        lines.append(f"- {key}={mask(value)}")
    for key, (old_val, new_val) in sorted(diff.changed.items()):
        lines.append(f"~ {key}: {mask(old_val)} -> {mask(new_val)}")

    if not lines:
        lines.append("(no changes)")
    return lines


def unified_diff(old_text: str, new_text: str, fromfile: str = "old", tofile: str = "new") -> str:
    """Return a unified diff string between two .env file texts."""
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(old_lines, new_lines, fromfile=fromfile, tofile=tofile)
    )
