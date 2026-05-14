"""Tests for envault.env_vars."""
import pytest
from pathlib import Path

from envault.env_vars import (
    EnvVarError,
    list_keys,
    get_value,
    set_value,
    delete_key,
)


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("# comment\nDB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=\"abc123\"\n")
    return f


# --- list_keys ---

def test_list_keys_returns_all_keys(env_file: Path) -> None:
    assert list_keys(env_file) == ["DB_HOST", "DB_PORT", "SECRET_KEY"]


def test_list_keys_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(EnvVarError, match="not found"):
        list_keys(tmp_path / "missing.env")


def test_list_keys_empty_file(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("# only comments\n\n")
    assert list_keys(f) == []


# --- get_value ---

def test_get_value_plain(env_file: Path) -> None:
    assert get_value(env_file, "DB_HOST") == "localhost"


def test_get_value_strips_double_quotes(env_file: Path) -> None:
    assert get_value(env_file, "SECRET_KEY") == "abc123"


def test_get_value_key_not_found_raises(env_file: Path) -> None:
    with pytest.raises(EnvVarError, match="Key not found"):
        get_value(env_file, "MISSING")


def test_get_value_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(EnvVarError, match="not found"):
        get_value(tmp_path / "missing.env", "KEY")


# --- set_value ---

def test_set_value_updates_existing_key(env_file: Path) -> None:
    updated = set_value(env_file, "DB_HOST", "remotehost")
    assert updated is True
    assert get_value(env_file, "DB_HOST") == "remotehost"


def test_set_value_adds_new_key(env_file: Path) -> None:
    updated = set_value(env_file, "NEW_KEY", "newval")
    assert updated is False
    assert get_value(env_file, "NEW_KEY") == "newval"


def test_set_value_preserves_other_keys(env_file: Path) -> None:
    set_value(env_file, "DB_HOST", "changed")
    assert get_value(env_file, "DB_PORT") == "5432"


def test_set_value_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(EnvVarError, match="not found"):
        set_value(tmp_path / "missing.env", "KEY", "val")


# --- delete_key ---

def test_delete_key_removes_entry(env_file: Path) -> None:
    delete_key(env_file, "DB_PORT")
    assert "DB_PORT" not in list_keys(env_file)


def test_delete_key_preserves_others(env_file: Path) -> None:
    delete_key(env_file, "DB_PORT")
    assert list_keys(env_file) == ["DB_HOST", "SECRET_KEY"]


def test_delete_key_not_found_raises(env_file: Path) -> None:
    with pytest.raises(EnvVarError, match="Key not found"):
        delete_key(env_file, "NONEXISTENT")


def test_delete_key_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(EnvVarError, match="not found"):
        delete_key(tmp_path / "missing.env", "KEY")
