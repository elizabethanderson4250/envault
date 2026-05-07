"""Tests for envault.compare."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.compare import (
    compare_vaults,
    format_compare,
    CompareError,
    CompareResult,
)
from envault.diff import EnvDiff
from envault.cli_compare import compare_group


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LEFT_PLAIN = "KEY_A=alpha\nKEY_B=beta\n"
_RIGHT_PLAIN = "KEY_A=alpha\nKEY_B=changed\nKEY_C=new\n"


def _fake_decrypt(path: str, passphrase=None) -> str:
    if "left" in path:
        return _LEFT_PLAIN
    return _RIGHT_PLAIN


# ---------------------------------------------------------------------------
# Unit tests — compare_vaults
# ---------------------------------------------------------------------------


def test_compare_missing_left_raises(tmp_path: Path) -> None:
    right = tmp_path / "right.env.gpg"
    right.touch()
    with pytest.raises(CompareError, match="not found"):
        compare_vaults(tmp_path / "missing.env.gpg", right)


def test_compare_missing_right_raises(tmp_path: Path) -> None:
    left = tmp_path / "left.env.gpg"
    left.touch()
    with pytest.raises(CompareError, match="not found"):
        compare_vaults(left, tmp_path / "missing.env.gpg")


def test_compare_decrypt_error_raises(tmp_path: Path) -> None:
    left = tmp_path / "left.env.gpg"
    right = tmp_path / "right.env.gpg"
    left.touch()
    right.touch()
    with patch("envault.compare.decrypt", side_effect=RuntimeError("gpg fail")):
        with pytest.raises(CompareError, match="Failed to decrypt"):
            compare_vaults(left, right)


def test_compare_detects_changes(tmp_path: Path) -> None:
    left = tmp_path / "left.env.gpg"
    right = tmp_path / "right.env.gpg"
    left.touch()
    right.touch()
    with patch("envault.compare.decrypt", side_effect=_fake_decrypt):
        result = compare_vaults(left, right)
    assert result.has_changes
    assert "KEY_C" in result.diff.added
    assert "KEY_B" in result.diff.changed
    assert result.left_keys == 2
    assert result.right_keys == 3


def test_compare_no_changes(tmp_path: Path) -> None:
    left = tmp_path / "left.env.gpg"
    right = tmp_path / "right.env.gpg"
    left.touch()
    right.touch()
    with patch("envault.compare.decrypt", return_value=_LEFT_PLAIN):
        result = compare_vaults(left, right)
    assert not result.has_changes


# ---------------------------------------------------------------------------
# Unit tests — format_compare
# ---------------------------------------------------------------------------


def test_format_compare_no_diff(tmp_path: Path) -> None:
    result = CompareResult(
        left_path=tmp_path / "a",
        right_path=tmp_path / "b",
        diff=EnvDiff(added=set(), removed=set(), changed={}, unchanged={}),
        left_keys=2,
        right_keys=2,
    )
    output = format_compare(result)
    assert "No differences" in output


def test_format_compare_shows_symbols(tmp_path: Path) -> None:
    diff = EnvDiff(
        added={"NEW_KEY"},
        removed={"OLD_KEY"},
        changed={"MOD_KEY": ("old", "new")},
        unchanged={},
    )
    result = CompareResult(
        left_path=tmp_path / "a",
        right_path=tmp_path / "b",
        diff=diff,
        left_keys=3,
        right_keys=3,
    )
    output = format_compare(result)
    assert "+ NEW_KEY" in output
    assert "- OLD_KEY" in output
    assert "~ MOD_KEY" in output


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_compare_no_diff(runner: CliRunner, tmp_path: Path) -> None:
    left = tmp_path / "left.env.gpg"
    right = tmp_path / "right.env.gpg"
    left.touch()
    right.touch()
    with patch("envault.compare.decrypt", return_value="KEY=val\n"):
        result = runner.invoke(compare_group, ["show", str(left), str(right)])
    assert result.exit_code == 0
    assert "No differences" in result.output


def test_cli_compare_exit_code_on_diff(runner: CliRunner, tmp_path: Path) -> None:
    left = tmp_path / "left.env.gpg"
    right = tmp_path / "right.env.gpg"
    left.touch()
    right.touch()
    with patch("envault.compare.decrypt", side_effect=_fake_decrypt):
        result = runner.invoke(
            compare_group, ["show", str(left), str(right), "--exit-code"]
        )
    assert result.exit_code == 1


def test_cli_compare_error_shown(runner: CliRunner, tmp_path: Path) -> None:
    left = tmp_path / "left.env.gpg"
    right = tmp_path / "right.env.gpg"
    left.touch()
    right.touch()
    with patch("envault.compare.decrypt", side_effect=RuntimeError("boom")):
        result = runner.invoke(compare_group, ["show", str(left), str(right)])
    assert result.exit_code != 0
    assert "Error" in result.output
