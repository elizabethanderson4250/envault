"""Tests for envault.cli_policy."""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from click.testing import CliRunner

from envault.cli_policy import policy_group
from envault.vault import Vault


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def vault_dir(tmp_path: Path) -> Path:
    v = Vault(tmp_path)
    v.add_recipient("AABBCCDDEEFF0011")
    return tmp_path


def test_show_policy_defaults(runner: CliRunner, vault_dir: Path) -> None:
    result = runner.invoke(policy_group, ["show", str(vault_dir)])
    assert result.exit_code == 0
    assert "required_keys" in result.output
    assert "min_recipients" in result.output


def test_set_policy_saves_file(runner: CliRunner, vault_dir: Path) -> None:
    result = runner.invoke(
        policy_group,
        ["set", "--require", "DB_URL", "--forbid", "PASSWORD", "--min-recipients", "1", str(vault_dir)],
    )
    assert result.exit_code == 0
    assert "Policy saved" in result.output
    data = json.loads((vault_dir / ".envault-policy.json").read_text())
    assert "DB_URL" in data["required_keys"]
    assert "PASSWORD" in data["forbidden_keys"]


def test_check_passes(runner: CliRunner, vault_dir: Path, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("DB_URL=postgres://localhost/db\n")
    runner.invoke(
        policy_group,
        ["set", "--require", "DB_URL", str(vault_dir)],
    )
    result = runner.invoke(policy_group, ["check", str(env_file), str(vault_dir)])
    assert result.exit_code == 0
    assert "passed" in result.output


def test_check_fails_on_violation(runner: CliRunner, vault_dir: Path, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("OTHER=value\n")
    runner.invoke(
        policy_group,
        ["set", "--require", "DB_URL", str(vault_dir)],
    )
    result = runner.invoke(policy_group, ["check", str(env_file), str(vault_dir)])
    assert result.exit_code != 0
    assert "DB_URL" in result.output


def test_check_forbidden_key_violation(runner: CliRunner, vault_dir: Path, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("PASSWORD=hunter2\n")
    runner.invoke(
        policy_group,
        ["set", "--forbid", "PASSWORD", str(vault_dir)],
    )
    result = runner.invoke(policy_group, ["check", str(env_file), str(vault_dir)])
    assert result.exit_code != 0
    assert "PASSWORD" in result.output
