"""prune.py — Remove stale or expired keys from a .env file."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple


class PruneError(Exception):
    """Raised when pruning fails."""


@dataclass
class PruneResult:
    removed: List[str] = field(default_factory=list)
    kept: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return len(self.removed) > 0


_BLANK_OR_COMMENT = re.compile(r"^\s*(#.*)?$")
_KEY_LINE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=")


def _key_of(line: str) -> str | None:
    m = _KEY_LINE.match(line)
    return m.group(1) if m else None


def prune_keys(
    env_path: Path,
    keys_to_remove: List[str],
    *,
    dry_run: bool = False,
) -> PruneResult:
    """Remove specific keys from *env_path*.

    Parameters
    ----------
    env_path:       Path to the .env file.
    keys_to_remove: Keys that should be deleted.
    dry_run:        If True the file is not modified.

    Returns a :class:`PruneResult` describing what was removed.
    """
    if not env_path.exists():
        raise PruneError(f"File not found: {env_path}")
    if not keys_to_remove:
        raise PruneError("keys_to_remove must not be empty")

    target = set(keys_to_remove)
    lines = env_path.read_text(encoding="utf-8").splitlines(keepends=True)

    result = PruneResult()
    kept_lines: List[str] = []

    for line in lines:
        key = _key_of(line)
        if key and key in target:
            result.removed.append(key)
        else:
            kept_lines.append(line)
            if key:
                result.kept.append(key)

    if result.changed and not dry_run:
        env_path.write_text("".join(kept_lines), encoding="utf-8")

    return result


def format_prune(result: PruneResult) -> str:
    """Return a human-readable summary of a :class:`PruneResult`."""
    if not result.changed:
        return "Nothing pruned."
    lines = [f"Pruned {len(result.removed)} key(s):"]
    for k in result.removed:
        lines.append(f"  - {k}")
    return "\n".join(lines)
