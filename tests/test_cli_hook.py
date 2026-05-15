"""Tests for envault.cli_hook."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli_hook import hook_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def _run(runner: CliRunner, vault_dir: Path, *args: str):
    return runner.invoke(hook_group, ["--vault-dir", str(vault_dir), *args])


def test_set_success(runner: CliRunner, vault_dir: Path) -> None:
    result = _run(runner, vault_dir, "set", "post-lock", "echo done")
    assert result.exit_code == 0
    assert "Hook set" in result.output


def test_set_invalid_event(runner: CliRunner, vault_dir: Path) -> None:
    result = _run(runner, vault_dir, "set", "bad-event", "echo hi")
    assert result.exit_code == 1
    assert "Error" in result.output


def test_remove_existing_hook(runner: CliRunner, vault_dir: Path) -> None:
    _run(runner, vault_dir, "set", "pre-lock", "echo hi")
    result = _run(runner, vault_dir, "remove", "pre-lock")
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_absent_hook(runner: CliRunner, vault_dir: Path) -> None:
    result = _run(runner, vault_dir, "remove", "pre-lock")
    assert result.exit_code == 0
    assert "No hook" in result.output


def test_list_empty(runner: CliRunner, vault_dir: Path) -> None:
    result = _run(runner, vault_dir, "list")
    assert result.exit_code == 0
    assert "No hooks" in result.output


def test_list_shows_hooks(runner: CliRunner, vault_dir: Path) -> None:
    _run(runner, vault_dir, "set", "post-rotate", "./notify.sh")
    result = _run(runner, vault_dir, "list")
    assert result.exit_code == 0
    assert "post-rotate" in result.output
    assert "./notify.sh" in result.output


def test_run_no_hook(runner: CliRunner, vault_dir: Path) -> None:
    result = _run(runner, vault_dir, "run", "post-lock")
    assert result.exit_code == 0
    assert "No hook" in result.output


def test_run_hook_success(runner: CliRunner, vault_dir: Path) -> None:
    _run(runner, vault_dir, "set", "post-lock", "true")
    with patch("envault.hook.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = _run(runner, vault_dir, "run", "post-lock")
    assert result.exit_code == 0
    assert "completed" in result.output


def test_run_hook_failure(runner: CliRunner, vault_dir: Path) -> None:
    _run(runner, vault_dir, "set", "post-lock", "false")
    with patch("envault.hook.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=2)
        result = _run(runner, vault_dir, "run", "post-lock")
    assert result.exit_code == 1
    assert "Error" in result.output
