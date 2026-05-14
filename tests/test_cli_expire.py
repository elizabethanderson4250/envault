"""Tests for envault.cli_expire."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_expire import expire_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    d = tmp_path / "vault"
    d.mkdir()
    return d


def test_set_creates_expiry(runner: CliRunner, vault_dir: Path) -> None:
    result = runner.invoke(expire_group, ["set", str(vault_dir), "--days", "7"])
    assert result.exit_code == 0
    assert "Expiry set" in result.output
    assert (vault_dir / ".expiry.json").exists()


def test_set_invalid_days_exits_nonzero(runner: CliRunner, vault_dir: Path) -> None:
    result = runner.invoke(expire_group, ["set", str(vault_dir), "--days", "0"])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_show_no_expiry(runner: CliRunner, vault_dir: Path) -> None:
    result = runner.invoke(expire_group, ["show", str(vault_dir)])
    assert result.exit_code == 0
    assert "No expiry" in result.output


def test_show_future_expiry(runner: CliRunner, vault_dir: Path) -> None:
    runner.invoke(expire_group, ["set", str(vault_dir), "--days", "30"])
    result = runner.invoke(expire_group, ["show", str(vault_dir)])
    assert result.exit_code == 0
    assert "Expires on" in result.output


def test_check_not_expired(runner: CliRunner, vault_dir: Path) -> None:
    runner.invoke(expire_group, ["set", str(vault_dir), "--days", "10"])
    result = runner.invoke(expire_group, ["check", str(vault_dir)])
    assert result.exit_code == 0
    assert "valid" in result.output


def test_check_expired_exits_1(runner: CliRunner, vault_dir: Path) -> None:
    past = datetime.now(timezone.utc) - timedelta(days=1)
    (vault_dir / ".expiry.json").write_text(json.dumps({"expires_at": past.isoformat()}))
    result = runner.invoke(expire_group, ["check", str(vault_dir)])
    assert result.exit_code == 1


def test_clear_removes_expiry(runner: CliRunner, vault_dir: Path) -> None:
    runner.invoke(expire_group, ["set", str(vault_dir), "--days", "5"])
    result = runner.invoke(expire_group, ["clear", str(vault_dir)])
    assert result.exit_code == 0
    assert "cleared" in result.output
    assert not (vault_dir / ".expiry.json").exists()


def test_clear_no_expiry_set(runner: CliRunner, vault_dir: Path) -> None:
    result = runner.invoke(expire_group, ["clear", str(vault_dir)])
    assert result.exit_code == 0
    assert "No expiry" in result.output
