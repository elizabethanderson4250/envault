"""Tests for envault.keys — key discovery and validation utilities."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from envault.keys import (
    KeyInfo,
    is_valid_fingerprint,
    list_public_keys,
    lookup_key,
)


# ---------------------------------------------------------------------------
# is_valid_fingerprint
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fp,expected", [
    ("ABCDEF1234567890", True),          # 16-char hex
    ("A" * 40, True),                    # 40-char hex (full fingerprint)
    ("abc123def456789a", True),          # lowercase
    ("SHORT", False),                    # too short
    ("ZZZZZZZZZZZZZZZZ", False),         # non-hex characters
    ("", False),
])
def test_is_valid_fingerprint(fp, expected):
    assert is_valid_fingerprint(fp) is expected


# ---------------------------------------------------------------------------
# KeyInfo helpers
# ---------------------------------------------------------------------------

def test_key_info_short_id():
    ki = KeyInfo(fingerprint="A" * 40, uids=["Alice <alice@example.com>"])
    assert ki.short_id() == "A" * 16


def test_key_info_primary_uid():
    ki = KeyInfo(fingerprint="A" * 16, uids=["Alice", "Bob"])
    assert ki.primary_uid() == "Alice"


def test_key_info_primary_uid_empty():
    ki = KeyInfo(fingerprint="A" * 16, uids=[])
    assert ki.primary_uid() == "<unknown>"


# ---------------------------------------------------------------------------
# lookup_key
# ---------------------------------------------------------------------------

def _colons_output(fp: str, uid: str) -> str:
    return (
        f"pub:u:4096:1:DEADBEEF12345678:2024-01-01:::u:::scESC:\n"
        f"fpr:::::::::{fp}:\n"
        f"uid:u::::2024-01-01::HASH::{uid}:\n"
    )


def test_lookup_key_invalid_fingerprint_raises():
    with pytest.raises(ValueError, match="Invalid fingerprint"):
        lookup_key("not-a-fingerprint")


def test_lookup_key_returns_key_info():
    fp = "A" * 40
    fake_proc = MagicMock(returncode=0, stdout=_colons_output(fp, "Alice <a@b.com>"), stderr="")
    with patch("envault.keys.subprocess.run", return_value=fake_proc) as mock_run:
        with patch("envault.keys._gpg_binary", return_value="gpg"):
            result = lookup_key(fp)
    assert result is not None
    assert result.fingerprint == fp
    assert result.uids == ["Alice <a@b.com>"]
    mock_run.assert_called_once()


def test_lookup_key_returns_none_when_not_found():
    import subprocess
    err = subprocess.CalledProcessError(2, "gpg", stderr="No public key")
    with patch("envault.keys.subprocess.run", side_effect=err):
        with patch("envault.keys._gpg_binary", return_value="gpg"):
            result = lookup_key("A" * 16)
    assert result is None


# ---------------------------------------------------------------------------
# list_public_keys
# ---------------------------------------------------------------------------

def test_list_public_keys_parses_multiple():
    fp1, fp2 = "A" * 40, "B" * 40
    stdout = (
        f"pub:u:4096:1:AAAA:2024-01-01::::\n"
        f"fpr:::::::::{fp1}:\n"
        f"uid:u::::2024-01-01::H1::Alice:\n"
        f"pub:u:4096:1:BBBB:2024-01-01::::\n"
        f"fpr:::::::::{fp2}:\n"
        f"uid:u::::2024-01-01::H2::Bob:\n"
    )
    fake_proc = MagicMock(returncode=0, stdout=stdout, stderr="")
    with patch("envault.keys.subprocess.run", return_value=fake_proc):
        with patch("envault.keys._gpg_binary", return_value="gpg"):
            keys = list_public_keys()
    assert len(keys) == 2
    assert keys[0].fingerprint == fp1
    assert keys[1].primary_uid() == "Bob"


def test_list_public_keys_empty_keyring():
    fake_proc = MagicMock(returncode=0, stdout="", stderr="")
    with patch("envault.keys.subprocess.run", return_value=fake_proc):
        with patch("envault.keys._gpg_binary", return_value="gpg"):
            keys = list_public_keys()
    assert keys == []
