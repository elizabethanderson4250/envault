"""Tag management for envault vaults.

Allows attaching and querying string tags (e.g. 'production', 'staging')
on a vault so teams can filter and identify environments quickly.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from envault.vault import Vault


class TagError(Exception):
    """Raised when a tag operation fails."""


_MAX_TAG_LENGTH = 64
_VALID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
)


def _validate_tag(tag: str) -> None:
    if not tag:
        raise TagError("Tag must not be empty.")
    if len(tag) > _MAX_TAG_LENGTH:
        raise TagError(f"Tag exceeds maximum length of {_MAX_TAG_LENGTH} characters.")
    invalid = set(tag) - _VALID_CHARS
    if invalid:
        raise TagError(
            f"Tag contains invalid characters: {', '.join(sorted(invalid))}"
        )


def get_tags(vault: Vault) -> List[str]:
    """Return the list of tags currently attached to *vault*."""
    return list(vault._meta.get("tags", []))


def add_tag(vault: Vault, tag: str) -> List[str]:
    """Add *tag* to *vault*. Returns the updated tag list.

    Raises TagError if the tag is invalid or already present.
    """
    _validate_tag(tag)
    tags: List[str] = vault._meta.setdefault("tags", [])
    if tag in tags:
        raise TagError(f"Tag '{tag}' is already attached to this vault.")
    tags.append(tag)
    vault._save_meta()
    return list(tags)


def remove_tag(vault: Vault, tag: str) -> List[str]:
    """Remove *tag* from *vault*. Returns the updated tag list.

    Raises TagError if the tag is not present.
    """
    tags: List[str] = vault._meta.get("tags", [])
    if tag not in tags:
        raise TagError(f"Tag '{tag}' is not attached to this vault.")
    tags.remove(tag)
    vault._meta["tags"] = tags
    vault._save_meta()
    return list(tags)


def format_tags(tags: List[str]) -> str:
    """Return a human-readable string listing *tags*."""
    if not tags:
        return "(no tags)"
    return ", ".join(sorted(tags))
