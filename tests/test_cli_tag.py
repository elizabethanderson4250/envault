"""Tests for envault.cli_tag CLI commands."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_tag import tag_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def test_add_tag_success(runner, vault_dir):
    result = runner.invoke(
        tag_group, ["add", "production", "--vault-dir", vault_dir]
    )
    assert result.exit_code == 0
    assert "production" in result.output


def test_add_tag_duplicate_shows_error(runner, vault_dir):
    runner.invoke(tag_group, ["add", "staging", "--vault-dir", vault_dir])
    result = runner.invoke(
        tag_group, ["add", "staging", "--vault-dir", vault_dir]
    )
    assert result.exit_code != 0
    assert "already attached" in result.output


def test_add_tag_invalid_shows_error(runner, vault_dir):
    result = runner.invoke(
        tag_group, ["add", "bad tag!", "--vault-dir", vault_dir]
    )
    assert result.exit_code != 0
    assert "invalid characters" in result.output


def test_remove_tag_success(runner, vault_dir):
    runner.invoke(tag_group, ["add", "production", "--vault-dir", vault_dir])
    result = runner.invoke(
        tag_group, ["remove", "production", "--vault-dir", vault_dir]
    )
    assert result.exit_code == 0
    assert "production" in result.output


def test_remove_nonexistent_tag_shows_error(runner, vault_dir):
    result = runner.invoke(
        tag_group, ["remove", "ghost", "--vault-dir", vault_dir]
    )
    assert result.exit_code != 0
    assert "not attached" in result.output


def test_list_tags_empty(runner, vault_dir):
    result = runner.invoke(tag_group, ["list", "--vault-dir", vault_dir])
    assert result.exit_code == 0
    assert "(no tags)" in result.output


def test_list_tags_shows_all(runner, vault_dir):
    runner.invoke(tag_group, ["add", "alpha", "--vault-dir", vault_dir])
    runner.invoke(tag_group, ["add", "beta", "--vault-dir", vault_dir])
    result = runner.invoke(tag_group, ["list", "--vault-dir", vault_dir])
    assert result.exit_code == 0
    assert "alpha" in result.output
    assert "beta" in result.output
