"""Tests for envault.snapshot."""

from __future__ import annotations

import pytest

from envault.snapshot import (
    SnapshotError,
    create_snapshot,
    delete_snapshot,
    read_snapshot,
    snapshot_exists,
    snapshot_path,
)


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n", encoding="utf-8")
    return p


def test_snapshot_path_returns_expected(tmp_path):
    p = snapshot_path(tmp_path)
    assert p == tmp_path / ".env.snapshot"


def test_create_snapshot_copies_file(tmp_path, env_file):
    dest = create_snapshot(env_file, tmp_path)
    assert dest.exists()
    assert dest.read_text() == env_file.read_text()


def test_create_snapshot_returns_path(tmp_path, env_file):
    dest = create_snapshot(env_file, tmp_path)
    assert dest == snapshot_path(tmp_path)


def test_create_snapshot_missing_source_raises(tmp_path):
    missing = tmp_path / "nonexistent.env"
    with pytest.raises(SnapshotError, match="not found"):
        create_snapshot(missing, tmp_path)


def test_read_snapshot_returns_content(tmp_path, env_file):
    create_snapshot(env_file, tmp_path)
    content = read_snapshot(tmp_path)
    assert "FOO=bar" in content


def test_read_snapshot_missing_raises(tmp_path):
    with pytest.raises(SnapshotError, match="No snapshot found"):
        read_snapshot(tmp_path)


def test_snapshot_exists_true(tmp_path, env_file):
    create_snapshot(env_file, tmp_path)
    assert snapshot_exists(tmp_path) is True


def test_snapshot_exists_false(tmp_path):
    assert snapshot_exists(tmp_path) is False


def test_delete_snapshot_removes_file(tmp_path, env_file):
    create_snapshot(env_file, tmp_path)
    result = delete_snapshot(tmp_path)
    assert result is True
    assert not snapshot_path(tmp_path).exists()


def test_delete_snapshot_returns_false_when_missing(tmp_path):
    result = delete_snapshot(tmp_path)
    assert result is False
