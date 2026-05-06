"""Lint .env files for common issues: duplicates, empty values, invalid names."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

_VALID_KEY_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


@dataclass
class LintIssue:
    line_no: int
    key: str | None
    code: str
    message: str


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0


def lint_env(path: Path) -> LintResult:
    """Parse and lint the .env file at *path*, returning a LintResult."""
    result = LintResult()

    if not path.exists():
        result.issues.append(LintIssue(0, None, "E001", f"File not found: {path}"))
        return result

    seen_keys: dict[str, int] = {}

    for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.strip()

        if not line or line.startswith('#'):
            continue

        if '=' not in line:
            result.issues.append(LintIssue(lineno, None, "E002",
                                            f"Line {lineno}: missing '=' separator"))
            continue

        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if not _VALID_KEY_RE.match(key):
            result.issues.append(LintIssue(lineno, key, "E003",
                                            f"Line {lineno}: invalid key name '{key}'"))

        if key in seen_keys:
            result.issues.append(LintIssue(lineno, key, "W001",
                                            f"Line {lineno}: duplicate key '{key}' "
                                            f"(first seen at line {seen_keys[key]})"))
        else:
            seen_keys[key] = lineno

        if value == '':
            result.issues.append(LintIssue(lineno, key, "W002",
                                            f"Line {lineno}: key '{key}' has an empty value"))

    return result


def format_lint(result: LintResult) -> str:
    """Return a human-readable string summarising *result*."""
    if result.ok:
        return "No issues found."
    lines = []
    for issue in result.issues:
        lines.append(f"[{issue.code}] {issue.message}")
    lines.append(f"\n{len(result.issues)} issue(s) found.")
    return "\n".join(lines)
