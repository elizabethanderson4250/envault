"""Merge two .env files with conflict detection and resolution strategies."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class MergeError(Exception):
    """Raised when a merge operation fails."""


class ConflictStrategy(str, Enum):
    OURS = "ours"       # Keep value from base file
    THEIRS = "theirs"   # Take value from incoming file
    UNION = "union"     # Keep both (incoming overwrites)


@dataclass
class MergeConflict:
    key: str
    base_value: str
    incoming_value: str


@dataclass
class MergeResult:
    merged: Dict[str, str] = field(default_factory=dict)
    conflicts: List[MergeConflict] = field(default_factory=list)
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)


def _parse_env(path: Path) -> Dict[str, str]:
    """Parse a .env file into a key->value dict."""
    if not path.exists():
        raise MergeError(f"File not found: {path}")
    result: Dict[str, str] = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        value = value.strip().strip('"').strip("'")
        result[key.strip()] = value
    return result


def merge_env(
    base: Path,
    incoming: Path,
    strategy: ConflictStrategy = ConflictStrategy.OURS,
) -> MergeResult:
    """Merge two .env files, detecting conflicts."""
    base_env = _parse_env(base)
    incoming_env = _parse_env(incoming)

    result = MergeResult(merged=dict(base_env))

    for key, inc_val in incoming_env.items():
        if key not in base_env:
            result.merged[key] = inc_val
            result.added.append(key)
        elif base_env[key] != inc_val:
            conflict = MergeConflict(key=key, base_value=base_env[key], incoming_value=inc_val)
            result.conflicts.append(conflict)
            if strategy == ConflictStrategy.THEIRS or strategy == ConflictStrategy.UNION:
                result.merged[key] = inc_val

    for key in base_env:
        if key not in incoming_env:
            result.removed.append(key)

    return result


def write_merged(result: MergeResult, output: Path) -> None:
    """Write merged key-value pairs to a .env file."""
    lines = [f"{k}={v}" for k, v in result.merged.items()]
    output.write_text("\n".join(lines) + "\n")


def format_merge_result(result: MergeResult) -> str:
    """Return a human-readable summary of the merge result."""
    parts: List[str] = []
    if result.added:
        parts.append(f"Added ({len(result.added)}): " + ", ".join(result.added))
    if result.removed:
        parts.append(f"Removed ({len(result.removed)}): " + ", ".join(result.removed))
    if result.conflicts:
        parts.append(f"Conflicts ({len(result.conflicts)}):")
        for c in result.conflicts:
            parts.append(f"  {c.key}: '{c.base_value}' vs '{c.incoming_value}'")
    if not parts:
        parts.append("No changes.")
    return "\n".join(parts)
