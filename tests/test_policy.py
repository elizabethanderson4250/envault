"""Tests for envault.policy."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.policy import (
    PolicyRule,
    PolicyViolation,
    PolicyError,
    load_policy,
    save_policy,
    check_policy,
    format_violations,
    _policy_path,
)


@pytest.fixture
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_policy_defaults_when_absent(vault_dir: Path) -> None:
    policy = load_policy(vault_dir)
    assert policy.required_keys == []
    assert policy.forbidden_keys == []
    assert policy.max_value_length is None
    assert policy.min_recipients == 1


def test_save_and_load_roundtrip(vault_dir: Path) -> None:
    policy = PolicyRule(
        required_keys=["DB_URL", "SECRET_KEY"],
        forbidden_keys=["PASSWORD"],
        max_value_length=128,
        min_recipients=2,
    )
    save_policy(vault_dir, policy)
    loaded = load_policy(vault_dir)
    assert loaded.required_keys == ["DB_URL", "SECRET_KEY"]
    assert loaded.forbidden_keys == ["PASSWORD"]
    assert loaded.max_value_length == 128
    assert loaded.min_recipients == 2


def test_load_policy_invalid_json_raises(vault_dir: Path) -> None:
    _policy_path(vault_dir).write_text("not json")
    with pytest.raises(PolicyError, match="Failed to read policy"):
        load_policy(vault_dir)


def test_check_policy_no_violations() -> None:
    policy = PolicyRule(required_keys=["A"], min_recipients=1)
    violations = check_policy(policy, {"A": "val"}, ["fp1"])
    assert violations == []


def test_check_policy_missing_required_key() -> None:
    policy = PolicyRule(required_keys=["DB_URL"])
    violations = check_policy(policy, {}, ["fp1"])
    assert len(violations) == 1
    assert violations[0].rule == "required_keys"
    assert "DB_URL" in violations[0].message


def test_check_policy_forbidden_key_present() -> None:
    policy = PolicyRule(forbidden_keys=["PASSWORD"])
    violations = check_policy(policy, {"PASSWORD": "secret"}, ["fp1"])
    assert len(violations) == 1
    assert violations[0].rule == "forbidden_keys"


def test_check_policy_value_too_long() -> None:
    policy = PolicyRule(max_value_length=5)
    violations = check_policy(policy, {"KEY": "toolongvalue"}, ["fp1"])
    assert any(v.rule == "max_value_length" for v in violations)


def test_check_policy_insufficient_recipients() -> None:
    policy = PolicyRule(min_recipients=3)
    violations = check_policy(policy, {}, ["fp1", "fp2"])
    assert any(v.rule == "min_recipients" for v in violations)


def test_format_violations_empty() -> None:
    assert format_violations([]) == "Policy check passed."


def test_format_violations_shows_messages() -> None:
    v = PolicyViolation(rule="required_keys", message="Missing required key: FOO")
    output = format_violations([v])
    assert "[required_keys]" in output
    assert "FOO" in output
