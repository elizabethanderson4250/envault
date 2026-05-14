"""Tests for envault.access."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.access import (
    ACCESS_FILENAME,
    AccessError,
    check_access,
    get_access,
    list_access,
    revoke_access,
    set_access,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


FP = "ABCDEF1234567890ABCDEF1234567890ABCDEF12"
FP2 = "1111111111111111111111111111111111111111"


def test_set_access_creates_file(vault_dir):
    set_access(vault_dir, FP, "read")
    assert (vault_dir / ACCESS_FILENAME).exists()


def test_set_access_stores_level(vault_dir):
    set_access(vault_dir, FP, "write")
    data = json.loads((vault_dir / ACCESS_FILENAME).read_text())
    assert data[FP] == "write"


def test_set_access_normalises_fingerprint(vault_dir):
    set_access(vault_dir, FP.lower(), "read")
    assert get_access(vault_dir, FP) == "read"


def test_set_access_invalid_level_raises(vault_dir):
    with pytest.raises(AccessError, match="Invalid level"):
        set_access(vault_dir, FP, "superuser")


def test_get_access_returns_none_when_absent(vault_dir):
    assert get_access(vault_dir, FP) is None


def test_get_access_returns_level(vault_dir):
    set_access(vault_dir, FP, "admin")
    assert get_access(vault_dir, FP) == "admin"


def test_revoke_returns_true_when_found(vault_dir):
    set_access(vault_dir, FP, "read")
    assert revoke_access(vault_dir, FP) is True
    assert get_access(vault_dir, FP) is None


def test_revoke_returns_false_when_absent(vault_dir):
    assert revoke_access(vault_dir, FP) is False


def test_list_access_empty(vault_dir):
    assert list_access(vault_dir) == []


def test_list_access_returns_sorted_entries(vault_dir):
    set_access(vault_dir, FP2, "read")
    set_access(vault_dir, FP, "admin")
    entries = list_access(vault_dir)
    assert len(entries) == 2
    assert entries[0]["fingerprint"] == FP
    assert entries[1]["fingerprint"] == FP2


def test_check_access_sufficient_level(vault_dir):
    set_access(vault_dir, FP, "write")
    assert check_access(vault_dir, FP, "read") is True
    assert check_access(vault_dir, FP, "write") is True
    assert check_access(vault_dir, FP, "admin") is False


def test_check_access_no_entry_returns_false(vault_dir):
    assert check_access(vault_dir, FP, "read") is False


def test_check_access_invalid_required_raises(vault_dir):
    with pytest.raises(AccessError, match="Unknown required level"):
        check_access(vault_dir, FP, "owner")


def test_corrupt_access_file_raises(vault_dir):
    (vault_dir / ACCESS_FILENAME).write_text("not json")
    with pytest.raises(AccessError, match="Corrupt"):
        list_access(vault_dir)
