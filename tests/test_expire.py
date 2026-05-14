"""Tests for envault.expire."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envault.expire import (
    ExpiryError,
    delete_expiry,
    format_expiry,
    is_expired,
    read_expiry,
    set_expiry,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    return vault_dir


def test_set_expiry_creates_file(vault_dir: Path) -> None:
    set_expiry(vault_dir, 7)
    assert (vault_dir / ".expiry.json").exists()


def test_set_expiry_returns_datetime(vault_dir: Path) -> None:
    result = set_expiry(vault_dir, 3)
    assert isinstance(result, datetime)
    assert result.tzinfo is not None


def test_set_expiry_zero_days_raises(vault_dir: Path) -> None:
    with pytest.raises(ExpiryError, match="positive"):
        set_expiry(vault_dir, 0)


def test_set_expiry_negative_days_raises(vault_dir: Path) -> None:
    with pytest.raises(ExpiryError):
        set_expiry(vault_dir, -5)


def test_read_expiry_none_when_absent(vault_dir: Path) -> None:
    assert read_expiry(vault_dir) is None


def test_read_expiry_returns_datetime(vault_dir: Path) -> None:
    set_expiry(vault_dir, 10)
    result = read_expiry(vault_dir)
    assert isinstance(result, datetime)


def test_read_expiry_corrupt_file_raises(vault_dir: Path) -> None:
    (vault_dir / ".expiry.json").write_text("not json")
    with pytest.raises(ExpiryError, match="Corrupt"):
        read_expiry(vault_dir)


def test_is_expired_false_when_no_expiry(vault_dir: Path) -> None:
    assert is_expired(vault_dir) is False


def test_is_expired_false_for_future(vault_dir: Path) -> None:
    set_expiry(vault_dir, 30)
    assert is_expired(vault_dir) is False


def test_is_expired_true_for_past(vault_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    set_expiry(vault_dir, 1)
    past = datetime.now(timezone.utc) - timedelta(days=2)
    import envault.expire as exp_mod
    monkeypatch.setattr(exp_mod, "_now_utc", lambda: past)
    # Manually write a past expiry
    import json
    expired_dt = datetime.now(timezone.utc) - timedelta(days=1)
    (vault_dir / ".expiry.json").write_text(json.dumps({"expires_at": expired_dt.isoformat()}))
    assert is_expired(vault_dir) is True


def test_delete_expiry_returns_true_when_present(vault_dir: Path) -> None:
    set_expiry(vault_dir, 5)
    assert delete_expiry(vault_dir) is True
    assert read_expiry(vault_dir) is None


def test_delete_expiry_returns_false_when_absent(vault_dir: Path) -> None:
    assert delete_expiry(vault_dir) is False


def test_format_expiry_no_expiry(vault_dir: Path) -> None:
    assert "No expiry" in format_expiry(vault_dir)


def test_format_expiry_future(vault_dir: Path) -> None:
    set_expiry(vault_dir, 14)
    msg = format_expiry(vault_dir)
    assert "Expires on" in msg
    assert "day(s)" in msg
