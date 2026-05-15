"""Tests for envault.lock_timeout."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from envault.lock_timeout import (
    LockTimeoutError,
    set_timeout,
    read_timeout,
    is_expired,
    clear_timeout,
    format_timeout,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    return vault_dir


def test_set_timeout_creates_file(vault_dir: Path) -> None:
    set_timeout(vault_dir, 30)
    assert (vault_dir / ".lock_timeout.json").exists()


def test_set_timeout_returns_future_datetime(vault_dir: Path) -> None:
    now = datetime.now(timezone.utc)
    expires_at = set_timeout(vault_dir, 10)
    assert expires_at > now
    assert expires_at <= now + timedelta(minutes=11)


def test_set_timeout_zero_raises(vault_dir: Path) -> None:
    with pytest.raises(LockTimeoutError, match="positive"):
        set_timeout(vault_dir, 0)


def test_set_timeout_negative_raises(vault_dir: Path) -> None:
    with pytest.raises(LockTimeoutError, match="positive"):
        set_timeout(vault_dir, -5)


def test_read_timeout_returns_none_when_absent(vault_dir: Path) -> None:
    assert read_timeout(vault_dir) is None


def test_read_timeout_returns_dict(vault_dir: Path) -> None:
    set_timeout(vault_dir, 15)
    data = read_timeout(vault_dir)
    assert data is not None
    assert data["minutes"] == 15
    assert "expires_at" in data


def test_read_timeout_invalid_json_raises(vault_dir: Path) -> None:
    (vault_dir / ".lock_timeout.json").write_text("not-json")
    with pytest.raises(LockTimeoutError, match="corrupt"):
        read_timeout(vault_dir)


def test_is_expired_false_for_future(vault_dir: Path) -> None:
    set_timeout(vault_dir, 60)
    assert is_expired(vault_dir) is False


def test_is_expired_true_for_past(vault_dir: Path) -> None:
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    data = {"minutes": 1, "expires_at": past.isoformat()}
    (vault_dir / ".lock_timeout.json").write_text(json.dumps(data))
    assert is_expired(vault_dir) is True


def test_is_expired_false_when_no_file(vault_dir: Path) -> None:
    assert is_expired(vault_dir) is False


def test_clear_timeout_removes_file(vault_dir: Path) -> None:
    set_timeout(vault_dir, 5)
    result = clear_timeout(vault_dir)
    assert result is True
    assert not (vault_dir / ".lock_timeout.json").exists()


def test_clear_timeout_returns_false_when_absent(vault_dir: Path) -> None:
    assert clear_timeout(vault_dir) is False


def test_format_timeout_active(vault_dir: Path) -> None:
    set_timeout(vault_dir, 120)
    data = read_timeout(vault_dir)
    assert data is not None
    result = format_timeout(data)
    assert "active" in result
    assert "120 min" in result


def test_format_timeout_expired(vault_dir: Path) -> None:
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    data = {"minutes": 5, "expires_at": past.isoformat()}
    result = format_timeout(data)
    assert "EXPIRED" in result
