"""Compare two encrypted vault files by decrypting and diffing their contents."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.crypto import decrypt
from envault.diff import parse_env, diff_env, EnvDiff


class CompareError(Exception):
    """Raised when vault comparison fails."""


@dataclass
class CompareResult:
    left_path: Path
    right_path: Path
    diff: EnvDiff
    left_keys: int = 0
    right_keys: int = 0

    @property
    def has_changes(self) -> bool:
        return bool(self.diff.added or self.diff.removed or self.diff.changed)


def _decrypt_to_env(path: Path, passphrase: Optional[str] = None) -> Dict[str, str]:
    """Decrypt a .env.gpg file and parse its key/value pairs."""
    if not path.exists():
        raise CompareError(f"File not found: {path}")
    try:
        plaintext = decrypt(str(path), passphrase=passphrase)
    except Exception as exc:
        raise CompareError(f"Failed to decrypt {path}: {exc}") from exc
    return parse_env(plaintext)


def compare_vaults(
    left: Path,
    right: Path,
    passphrase: Optional[str] = None,
) -> CompareResult:
    """Compare two encrypted vault files and return a CompareResult."""
    left_env = _decrypt_to_env(left, passphrase)
    right_env = _decrypt_to_env(right, passphrase)
    diff = diff_env(left_env, right_env)
    return CompareResult(
        left_path=left,
        right_path=right,
        diff=diff,
        left_keys=len(left_env),
        right_keys=len(right_env),
    )


def format_compare(result: CompareResult) -> str:
    """Format a CompareResult as a human-readable string."""
    lines: List[str] = [
        f"Comparing:",
        f"  left : {result.left_path}",
        f"  right: {result.right_path}",
        f"  keys : {result.left_keys} → {result.right_keys}",
        "",
    ]
    if not result.has_changes:
        lines.append("No differences found.")
        return "\n".join(lines)
    for key in sorted(result.diff.added):
        lines.append(f"+ {key}")
    for key in sorted(result.diff.removed):
        lines.append(f"- {key}")
    for key, (old, new) in sorted(result.diff.changed.items()):
        lines.append(f"~ {key}: {old!r} → {new!r}")
    return "\n".join(lines)
