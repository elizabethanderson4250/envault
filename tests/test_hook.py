"""Tests for envault.hook."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.hook import (
    HOOK_EVENTS,
    HookError,
    get_hook,
    list_hooks,
    remove_hook,
    run_hook,
    set_hook,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_set_hook_creates_file(vault_dir: Path) -> None:
    set_hook(vault_dir, "post-lock", "echo locked")
    hooks_file = vault_dir / ".envault" / "hooks.json"
    assert hooks_file.exists()
    data = json.loads(hooks_file.read_text())
    assert data["post-lock"] == "echo locked"


def test_set_hook_invalid_event_raises(vault_dir: Path) -> None:
    with pytest.raises(HookError, match="Unknown event"):
        set_hook(vault_dir, "not-an-event", "echo hi")


def test_set_hook_overwrites_existing(vault_dir: Path) -> None:
    set_hook(vault_dir, "pre-lock", "echo first")
    set_hook(vault_dir, "pre-lock", "echo second")
    assert get_hook(vault_dir, "pre-lock") == "echo second"


def test_get_hook_returns_none_when_absent(vault_dir: Path) -> None:
    assert get_hook(vault_dir, "post-lock") is None


def test_get_hook_returns_command(vault_dir: Path) -> None:
    set_hook(vault_dir, "post-rotate", "./notify.sh")
    assert get_hook(vault_dir, "post-rotate") == "./notify.sh"


def test_remove_hook_returns_true_when_present(vault_dir: Path) -> None:
    set_hook(vault_dir, "pre-unlock", "echo hi")
    assert remove_hook(vault_dir, "pre-unlock") is True
    assert get_hook(vault_dir, "pre-unlock") is None


def test_remove_hook_returns_false_when_absent(vault_dir: Path) -> None:
    assert remove_hook(vault_dir, "pre-unlock") is False


def test_list_hooks_empty_when_no_file(vault_dir: Path) -> None:
    assert list_hooks(vault_dir) == {}


def test_list_hooks_returns_all(vault_dir: Path) -> None:
    set_hook(vault_dir, "pre-lock", "echo a")
    set_hook(vault_dir, "post-lock", "echo b")
    hooks = list_hooks(vault_dir)
    assert hooks == {"pre-lock": "echo a", "post-lock": "echo b"}


def test_load_invalid_json_raises(vault_dir: Path) -> None:
    p = vault_dir / ".envault" / "hooks.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{not valid json")
    with pytest.raises(HookError, match="Invalid hooks.json"):
        list_hooks(vault_dir)


def test_run_hook_returns_none_when_no_hook(vault_dir: Path) -> None:
    assert run_hook(vault_dir, "post-lock") is None


def test_run_hook_success(vault_dir: Path) -> None:
    set_hook(vault_dir, "post-lock", "true")
    with patch("envault.hook.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        code = run_hook(vault_dir, "post-lock")
    assert code == 0


def test_run_hook_failure_raises(vault_dir: Path) -> None:
    set_hook(vault_dir, "post-lock", "false")
    with patch("envault.hook.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        with pytest.raises(HookError, match="failed with exit code 1"):
            run_hook(vault_dir, "post-lock")
