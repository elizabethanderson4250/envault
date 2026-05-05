"""Search and filter env keys across a vault."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class SearchError(Exception):
    """Raised when a search operation fails."""


@dataclass
class SearchResult:
    """A single match from a search over env key/value pairs."""

    key: str
    value: str
    line_number: int
    matched_on: str  # 'key' | 'value' | 'both'


def parse_env_lines(text: str) -> Dict[int, tuple]:
    """Return {line_number: (key, value)} for non-comment, non-blank lines."""
    result: Dict[int, tuple] = {}
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        result[lineno] = (key.strip(), value)
    return result


def search_env(
    text: str,
    pattern: str,
    *,
    search_keys: bool = True,
    search_values: bool = False,
    case_sensitive: bool = False,
) -> List[SearchResult]:
    """Search env text for *pattern* (substring or regex).

    Parameters
    ----------
    text:           Raw contents of a decrypted .env file.
    pattern:        Regex pattern to search for.
    search_keys:    Whether to match against key names (default True).
    search_values:  Whether to match against values (default False).
    case_sensitive: Use case-sensitive matching (default False).
    """
    if not pattern:
        raise SearchError("Search pattern must not be empty.")

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        compiled = re.compile(pattern, flags)
    except re.error as exc:
        raise SearchError(f"Invalid regex pattern: {exc}") from exc

    results: List[SearchResult] = []
    for lineno, (key, value) in parse_env_lines(text).items():
        key_match = search_keys and bool(compiled.search(key))
        val_match = search_values and bool(compiled.search(value))
        if key_match or val_match:
            if key_match and val_match:
                matched_on = "both"
            elif key_match:
                matched_on = "key"
            else:
                matched_on = "value"
            results.append(
                SearchResult(
                    key=key,
                    value=value,
                    line_number=lineno,
                    matched_on=matched_on,
                )
            )
    return results


def format_results(results: List[SearchResult], *, show_values: bool = False) -> str:
    """Return a human-readable string of search results."""
    if not results:
        return "No matches found."
    lines = []
    for r in results:
        val_part = f"={r.value}" if show_values else ""
        lines.append(f"  line {r.line_number:>4}: {r.key}{val_part}  [{r.matched_on}]")
    return "\n".join(lines)
