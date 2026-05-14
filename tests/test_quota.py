"""Tests for envault.quota."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.quota import (
    DEFAULT_MAX_KEYS,
    QuotaError,
    QuotaResult,
    check_quota,
    delete_quota,
    format_quota,
    read_quota,
    set_quota,
)
from envault.cli_quota import quota_group


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("KEY1=val1\nKEY2=val2\n# comment\n\nKEY3=val3\n")
    return p


def test_set_quota_creates_file(vault_dir: Path) -> None:
    set_quota(vault_dir, 50)
    assert (vault_dir / ".envault_quota.json").exists()


def test_set_quota_zero_raises(vault_dir: Path) -> None:
    with pytest.raises(QuotaError, match="at least 1"):
        set_quota(vault_dir, 0)


def test_set_quota_negative_raises(vault_dir: Path) -> None:
    with pytest.raises(QuotaError):
        set_quota(vault_dir, -5)


def test_read_quota_returns_default_when_absent(vault_dir: Path) -> None:
    assert read_quota(vault_dir) == DEFAULT_MAX_KEYS


def test_read_quota_returns_set_value(vault_dir: Path) -> None:
    set_quota(vault_dir, 25)
    assert read_quota(vault_dir) == 25


def test_read_quota_corrupt_raises(vault_dir: Path) -> None:
    (vault_dir / ".envault_quota.json").write_text("not-json")
    with pytest.raises(QuotaError, match="Corrupt"):
        read_quota(vault_dir)


def test_delete_quota_returns_true_when_existed(vault_dir: Path) -> None:
    set_quota(vault_dir, 10)
    assert delete_quota(vault_dir) is True
    assert not (vault_dir / ".envault_quota.json").exists()


def test_delete_quota_returns_false_when_absent(vault_dir: Path) -> None:
    assert delete_quota(vault_dir) is False


def test_check_quota_ok(vault_dir: Path, env_file: Path) -> None:
    set_quota(vault_dir, 10)
    result = check_quota(vault_dir, env_file)
    assert result.key_count == 3
    assert result.max_keys == 10
    assert not result.exceeded
    assert result.remaining == 7


def test_check_quota_exceeded(vault_dir: Path, env_file: Path) -> None:
    set_quota(vault_dir, 2)
    result = check_quota(vault_dir, env_file)
    assert result.exceeded
    assert result.remaining == 0


def test_check_quota_missing_env_raises(vault_dir: Path) -> None:
    with pytest.raises(QuotaError, match="not found"):
        check_quota(vault_dir, vault_dir / "nonexistent.env")


def test_format_quota_ok() -> None:
    r = QuotaResult(key_count=5, max_keys=20)
    out = format_quota(r)
    assert "OK" in out
    assert "5 / 20" in out


def test_format_quota_exceeded() -> None:
    r = QuotaResult(key_count=25, max_keys=20)
    out = format_quota(r)
    assert "EXCEEDED" in out


# --- CLI tests ---

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_set_and_show(runner: CliRunner, vault_dir: Path) -> None:
    r = runner.invoke(quota_group, ["set", str(vault_dir), "42"])
    assert r.exit_code == 0
    assert "42" in r.output
    r2 = runner.invoke(quota_group, ["show", str(vault_dir)])
    assert "42" in r2.output


def test_cli_check_ok(runner: CliRunner, vault_dir: Path, env_file: Path) -> None:
    runner.invoke(quota_group, ["set", str(vault_dir), "10"])
    r = runner.invoke(quota_group, ["check", str(vault_dir), str(env_file)])
    assert r.exit_code == 0
    assert "OK" in r.output


def test_cli_check_exceeded(runner: CliRunner, vault_dir: Path, env_file: Path) -> None:
    runner.invoke(quota_group, ["set", str(vault_dir), "1"])
    r = runner.invoke(quota_group, ["check", str(vault_dir), str(env_file)])
    assert r.exit_code != 0


def test_cli_clear(runner: CliRunner, vault_dir: Path) -> None:
    runner.invoke(quota_group, ["set", str(vault_dir), "5"])
    r = runner.invoke(quota_group, ["clear", str(vault_dir)])
    assert "cleared" in r.output
    assert read_quota(vault_dir) == DEFAULT_MAX_KEYS
