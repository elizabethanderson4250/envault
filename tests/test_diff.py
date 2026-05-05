"""Tests for envault.diff."""

from __future__ import annotations

import pytest

from envault.diff import EnvDiff, diff_env, format_diff, parse_env, unified_diff


ENV_OLD = """\
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=old_secret
DEBUG=true
"""

ENV_NEW = """\
DB_HOST=localhost
DB_PORT=5433
SECRET_KEY=new_secret
API_TOKEN=abc123
"""


def test_parse_env_basic():
    result = parse_env("FOO=bar\nBAZ=qux\n")
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_ignores_comments_and_blanks():
    text = "# comment\n\nFOO=bar\n"
    assert parse_env(text) == {"FOO": "bar"}


def test_parse_env_strips_quotes():
    assert parse_env('KEY="value"') == {"KEY": "value"}
    assert parse_env("KEY='value'") == {"KEY": "value"}


def test_parse_env_no_value_line_ignored():
    assert parse_env("NOEQUALS\n") == {}


def test_diff_env_detects_added():
    d = diff_env(ENV_OLD, ENV_NEW)
    assert "API_TOKEN" in d.added
    assert d.added["API_TOKEN"] == "abc123"


def test_diff_env_detects_removed():
    d = diff_env(ENV_OLD, ENV_NEW)
    assert "DEBUG" in d.removed


def test_diff_env_detects_changed():
    d = diff_env(ENV_OLD, ENV_NEW)
    assert "DB_PORT" in d.changed
    assert d.changed["DB_PORT"] == ("5432", "5433")
    assert "SECRET_KEY" in d.changed


def test_diff_env_detects_unchanged():
    d = diff_env(ENV_OLD, ENV_NEW)
    assert "DB_HOST" in d.unchanged


def test_has_changes_true():
    d = diff_env(ENV_OLD, ENV_NEW)
    assert d.has_changes is True


def test_has_changes_false():
    d = diff_env(ENV_OLD, ENV_OLD)
    assert d.has_changes is False


def test_format_diff_masks_values():
    d = diff_env(ENV_OLD, ENV_NEW)
    lines = format_diff(d, mask_values=True)
    combined = "\n".join(lines)
    assert "***" in combined
    assert "old_secret" not in combined


def test_format_diff_reveals_values():
    d = diff_env(ENV_OLD, ENV_NEW)
    lines = format_diff(d, mask_values=False)
    combined = "\n".join(lines)
    assert "old_secret" in combined or "new_secret" in combined


def test_format_diff_no_changes_message():
    d = diff_env(ENV_OLD, ENV_OLD)
    lines = format_diff(d)
    assert lines == ["(no changes)"]


def test_unified_diff_returns_string():
    result = unified_diff(ENV_OLD, ENV_NEW)
    assert isinstance(result, str)
    assert "+" in result or "-" in result


def test_unified_diff_identical_returns_empty():
    result = unified_diff(ENV_OLD, ENV_OLD)
    assert result == ""
