"""Tests for envault.tag module."""
from __future__ import annotations

import pytest

from envault.vault import Vault
from envault.tag import (
    TagError,
    add_tag,
    remove_tag,
    get_tags,
    format_tags,
    _validate_tag,
)


@pytest.fixture()
def vault(tmp_path):
    return Vault(str(tmp_path))


# ---------------------------------------------------------------------------
# _validate_tag
# ---------------------------------------------------------------------------

def test_validate_tag_empty_raises():
    with pytest.raises(TagError, match="empty"):
        _validate_tag("")


def test_validate_tag_too_long_raises():
    with pytest.raises(TagError, match="maximum length"):
        _validate_tag("a" * 65)


def test_validate_tag_invalid_chars_raises():
    with pytest.raises(TagError, match="invalid characters"):
        _validate_tag("bad tag!")


def test_validate_tag_valid_passes():
    _validate_tag("production")
    _validate_tag("staging-v2")
    _validate_tag("team.alpha_01")


# ---------------------------------------------------------------------------
# get_tags / add_tag
# ---------------------------------------------------------------------------

def test_get_tags_empty_by_default(vault):
    assert get_tags(vault) == []


def test_add_tag_returns_updated_list(vault):
    result = add_tag(vault, "production")
    assert "production" in result


def test_add_tag_persists(vault):
    add_tag(vault, "staging")
    # Re-load vault from same directory
    vault2 = Vault(vault.path)
    assert "staging" in get_tags(vault2)


def test_add_duplicate_tag_raises(vault):
    add_tag(vault, "production")
    with pytest.raises(TagError, match="already attached"):
        add_tag(vault, "production")


def test_add_multiple_tags(vault):
    add_tag(vault, "alpha")
    add_tag(vault, "beta")
    assert set(get_tags(vault)) == {"alpha", "beta"}


# ---------------------------------------------------------------------------
# remove_tag
# ---------------------------------------------------------------------------

def test_remove_tag_success(vault):
    add_tag(vault, "production")
    result = remove_tag(vault, "production")
    assert "production" not in result


def test_remove_tag_persists(vault):
    add_tag(vault, "staging")
    remove_tag(vault, "staging")
    vault2 = Vault(vault.path)
    assert get_tags(vault2) == []


def test_remove_nonexistent_tag_raises(vault):
    with pytest.raises(TagError, match="not attached"):
        remove_tag(vault, "ghost")


# ---------------------------------------------------------------------------
# format_tags
# ---------------------------------------------------------------------------

def test_format_tags_empty():
    assert format_tags([]) == "(no tags)"


def test_format_tags_sorted():
    result = format_tags(["zebra", "alpha", "mango"])
    assert result == "alpha, mango, zebra"
