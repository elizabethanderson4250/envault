"""Tests for envault.rename."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.rename import rename_key, RenameError


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "# a comment\n"
        "API_KEY=secret\n",
        encoding="utf-8",
    )
    return p


def test_rename_key_basic(env_file: Path) -> None:
    lineno = rename_key(env_file, "DB_HOST", "DATABASE_HOST")
    text = env_file.read_text()
    assert "DATABASE_HOST=localhost" in text
    assert "DB_HOST" not in text
    assert lineno == 1


def test_rename_key_preserves_other_lines(env_file: Path) -> None:
    rename_key(env_file, "API_KEY", "API_TOKEN")
    text = env_file.read_text()
    assert "DB_HOST=localhost" in text
    assert "DB_PORT=5432" in text
    assert "# a comment" in text
    assert "API_TOKEN=secret" in text


def test_rename_key_missing_file(tmp_path: Path) -> None:
    with pytest.raises(RenameError, match="not found"):
        rename_key(tmp_path / "missing.env", "FOO", "BAR")


def test_rename_key_not_found(env_file: Path) -> None:
    with pytest.raises(RenameError, match="MISSING_KEY.*not found"):
        rename_key(env_file, "MISSING_KEY", "OTHER")


def test_rename_key_new_key_exists_raises(env_file: Path) -> None:
    with pytest.raises(RenameError, match="already exists"):
        rename_key(env_file, "DB_HOST", "DB_PORT")


def test_rename_key_new_key_exists_overwrite(env_file: Path) -> None:
    rename_key(env_file, "DB_HOST", "DB_PORT", overwrite=True)
    text = env_file.read_text()
    # Original DB_PORT line replaced, only one DB_PORT remains
    assert text.count("DB_PORT") == 1
    assert "DB_PORT=localhost" in text
    assert "DB_HOST" not in text


def test_rename_invalid_old_key(env_file: Path) -> None:
    with pytest.raises(RenameError, match="Invalid key name"):
        rename_key(env_file, "123BAD", "GOOD")


def test_rename_invalid_new_key(env_file: Path) -> None:
    with pytest.raises(RenameError, match="Invalid key name"):
        rename_key(env_file, "DB_HOST", "bad-key")


def test_rename_comment_line_ignored(env_file: Path) -> None:
    """Lines starting with # should not be treated as key definitions."""
    with pytest.raises(RenameError, match="not found"):
        rename_key(env_file, "a comment", "OTHER")


def test_rename_returns_correct_lineno(env_file: Path) -> None:
    lineno = rename_key(env_file, "API_KEY", "API_TOKEN")
    assert lineno == 4
