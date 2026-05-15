"""Tests for envault.notify."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.notify import (
    NotifyConfig,
    NotifyError,
    load_config,
    save_config,
    send_notification,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# save_config / load_config
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(vault_dir):
    cfg = NotifyConfig(channel="file", target="/tmp/out.log", events=["lock", "rotate"])
    save_config(vault_dir, cfg)
    loaded = load_config(vault_dir)
    assert loaded is not None
    assert loaded.channel == "file"
    assert loaded.target == "/tmp/out.log"
    assert loaded.events == ["lock", "rotate"]


def test_load_config_returns_none_when_absent(vault_dir):
    assert load_config(vault_dir) is None


def test_save_config_invalid_channel_raises(vault_dir):
    cfg = NotifyConfig(channel="sms", target="", events=[])
    with pytest.raises(NotifyError, match="Invalid channel"):
        save_config(vault_dir, cfg)


def test_load_config_invalid_json_raises(vault_dir):
    cfg_path = vault_dir / ".envault" / "notify.json"
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text("not-json")
    with pytest.raises(NotifyError):
        load_config(vault_dir)


# ---------------------------------------------------------------------------
# send_notification
# ---------------------------------------------------------------------------

def test_send_notification_no_config_returns_false(vault_dir):
    result = send_notification(vault_dir, "lock", "vault locked")
    assert result is False


def test_send_notification_stdout_returns_true(vault_dir, capsys):
    save_config(vault_dir, NotifyConfig(channel="stdout", target="", events=[]))
    result = send_notification(vault_dir, "lock", "vault locked")
    assert result is True
    captured = capsys.readouterr()
    assert "lock" in captured.out
    assert "vault locked" in captured.out


def test_send_notification_filtered_by_event(vault_dir, capsys):
    save_config(vault_dir, NotifyConfig(channel="stdout", target="", events=["rotate"]))
    result = send_notification(vault_dir, "lock", "vault locked")
    assert result is False


def test_send_notification_file_channel(vault_dir, tmp_path):
    log_file = tmp_path / "notify.log"
    save_config(vault_dir, NotifyConfig(channel="file", target=str(log_file), events=[]))
    send_notification(vault_dir, "lock", "done")
    assert log_file.exists()
    assert "lock" in log_file.read_text()


def test_send_notification_exec_channel(vault_dir):
    save_config(vault_dir, NotifyConfig(channel="exec", target="/usr/bin/true", events=[]))
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = send_notification(vault_dir, "rotate", "keys rotated")
    assert result is True
    mock_run.assert_called_once()


def test_send_notification_exec_failure_raises(vault_dir):
    save_config(vault_dir, NotifyConfig(channel="exec", target="/usr/bin/false", events=[]))
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd")):
        with pytest.raises(NotifyError, match="Notification command failed"):
            send_notification(vault_dir, "lock", "msg")
