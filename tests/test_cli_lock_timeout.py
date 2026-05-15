"""Tests for envault.cli_lock_timeout CLI commands."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_lock_timeout import lock_timeout_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    d = tmp_path / "vault"
    d.mkdir()
    return d


def _run(runner: CliRunner, *args: str):
    return runner.invoke(lock_timeout_group, list(args), catch_exceptions=False)


def test_set_success(runner: CliRunner, vault_dir: Path) -> None:
    result = _run(runner, "set", str(vault_dir), "30")
    assert result.exit_code == 0
    assert "30 min" in result.output
    assert (vault_dir / ".lock_timeout.json").exists()


def test_set_invalid_minutes_exits_nonzero(runner: CliRunner, vault_dir: Path) -> None:
    result = runner.invoke(lock_timeout_group, ["set", str(vault_dir), "0"])
    assert result.exit_code != 0


def test_show_no_timeout(runner: CliRunner, vault_dir: Path) -> None:
    result = _run(runner, "show", str(vault_dir))
    assert result.exit_code == 0
    assert "No lock timeout" in result.output


def test_show_existing_timeout(runner: CliRunner, vault_dir: Path) -> None:
    _run(runner, "set", str(vault_dir), "45")
    result = _run(runner, "show", str(vault_dir))
    assert result.exit_code == 0
    assert "45 min" in result.output


def test_check_not_expired(runner: CliRunner, vault_dir: Path) -> None:
    _run(runner, "set", str(vault_dir), "60")
    result = _run(runner, "check", str(vault_dir))
    assert result.exit_code == 0
    assert "not expired" in result.output


def test_check_expired(runner: CliRunner, vault_dir: Path) -> None:
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    data = {"minutes": 1, "expires_at": past.isoformat()}
    (vault_dir / ".lock_timeout.json").write_text(json.dumps(data))
    result = runner.invoke(lock_timeout_group, ["check", str(vault_dir)])
    assert result.exit_code == 1


def test_clear_existing(runner: CliRunner, vault_dir: Path) -> None:
    _run(runner, "set", str(vault_dir), "10")
    result = _run(runner, "clear", str(vault_dir))
    assert result.exit_code == 0
    assert "cleared" in result.output
    assert not (vault_dir / ".lock_timeout.json").exists()


def test_clear_absent(runner: CliRunner, vault_dir: Path) -> None:
    result = _run(runner, "clear", str(vault_dir))
    assert result.exit_code == 0
    assert "No lock timeout" in result.output
