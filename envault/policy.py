"""Policy enforcement: define and check rules for .env files."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

POLICY_FILENAME = ".envault-policy.json"


class PolicyError(Exception):
    """Raised when a policy operation fails."""


@dataclass
class PolicyRule:
    required_keys: List[str] = field(default_factory=list)
    forbidden_keys: List[str] = field(default_factory=list)
    max_value_length: Optional[int] = None
    min_recipients: int = 1


@dataclass
class PolicyViolation:
    rule: str
    message: str


def _policy_path(vault_dir: Path) -> Path:
    return vault_dir / POLICY_FILENAME


def load_policy(vault_dir: Path) -> PolicyRule:
    """Load policy from vault directory. Returns default if absent."""
    path = _policy_path(vault_dir)
    if not path.exists():
        return PolicyRule()
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise PolicyError(f"Failed to read policy: {exc}") from exc
    return PolicyRule(
        required_keys=data.get("required_keys", []),
        forbidden_keys=data.get("forbidden_keys", []),
        max_value_length=data.get("max_value_length"),
        min_recipients=data.get("min_recipients", 1),
    )


def save_policy(vault_dir: Path, policy: PolicyRule) -> None:
    """Persist policy to the vault directory."""
    path = _policy_path(vault_dir)
    data: Dict = {
        "required_keys": policy.required_keys,
        "forbidden_keys": policy.forbidden_keys,
        "min_recipients": policy.min_recipients,
    }
    if policy.max_value_length is not None:
        data["max_value_length"] = policy.max_value_length
    try:
        path.write_text(json.dumps(data, indent=2))
    except OSError as exc:
        raise PolicyError(f"Failed to write policy: {exc}") from exc


def check_policy(
    policy: PolicyRule,
    env: Dict[str, str],
    recipients: List[str],
) -> List[PolicyViolation]:
    """Return a list of violations; empty list means compliant."""
    violations: List[PolicyViolation] = []
    for key in policy.required_keys:
        if key not in env:
            violations.append(PolicyViolation("required_keys", f"Missing required key: {key}"))
    for key in policy.forbidden_keys:
        if key in env:
            violations.append(PolicyViolation("forbidden_keys", f"Forbidden key present: {key}"))
    if policy.max_value_length is not None:
        for key, value in env.items():
            if len(value) > policy.max_value_length:
                violations.append(
                    PolicyViolation(
                        "max_value_length",
                        f"Value for '{key}' exceeds max length {policy.max_value_length}",
                    )
                )
    if len(recipients) < policy.min_recipients:
        violations.append(
            PolicyViolation(
                "min_recipients",
                f"At least {policy.min_recipients} recipient(s) required, got {len(recipients)}",
            )
        )
    return violations


def format_violations(violations: List[PolicyViolation]) -> str:
    if not violations:
        return "Policy check passed."
    lines = ["Policy violations:"]
    for v in violations:
        lines.append(f"  [{v.rule}] {v.message}")
    return "\n".join(lines)
