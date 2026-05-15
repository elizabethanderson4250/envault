"""Tests for envault.rekey."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.rekey import rekey, RekeyError
from envault.vault import Vault


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    v = Vault(tmp_path)
    v.set_recipients(["AAAA1111AAAA1111AAAA1111AAAA1111AAAA1111"])
    return tmp_path


@pytest.fixture()
def vault_with_file(vault_dir: Path) -> Path:
    (vault_dir / "vault.env.gpg").write_bytes(b"ENCRYPTED")
    return vault_dir


def test_rekey_no_recipients_raises(vault_with_file: Path) -> None:
    with pytest.raises(RekeyError, match="must not be empty"):
        rekey(vault_with_file, [])


def test_rekey_missing_vault_file_raises(vault_dir: Path) -> None:
    with pytest.raises(RekeyError, match="not found"):
        rekey(vault_dir, ["BBBB2222BBBB2222BBBB2222BBBB2222BBBB2222"])


def test_rekey_decrypt_failure_raises(vault_with_file: Path) -> None:
    from envault.crypto import GPGError

    with patch("envault.rekey.decrypt", side_effect=GPGError("bad decrypt")):
        with pytest.raises(RekeyError, match="Failed to decrypt"):
            rekey(vault_with_file, ["BBBB2222BBBB2222BBBB2222BBBB2222BBBB2222"])


def test_rekey_encrypt_failure_raises(vault_with_file: Path) -> None:
    from envault.crypto import GPGError

    with patch("envault.rekey.decrypt", return_value=b"plain"):
        with patch("envault.rekey.encrypt", side_effect=GPGError("bad enc")):
            with pytest.raises(RekeyError, match="Failed to re-encrypt"):
                rekey(vault_with_file, ["BBBB2222BBBB2222BBBB2222BBBB2222BBBB2222"])


def test_rekey_success_writes_file(vault_with_file: Path) -> None:
    new_fp = "BBBB2222BBBB2222BBBB2222BBBB2222BBBB2222"
    with patch("envault.rekey.decrypt", return_value=b"plain") as mock_dec:
        with patch("envault.rekey.encrypt", return_value=b"NEWENC") as mock_enc:
            result = rekey(vault_with_file, [new_fp])

    assert result == vault_with_file / "vault.env.gpg"
    assert result.read_bytes() == b"NEWENC"
    mock_dec.assert_called_once()
    mock_enc.assert_called_once_with(b"plain", recipients=[new_fp])


def test_rekey_updates_recipients(vault_with_file: Path) -> None:
    new_fp = "CCCC3333CCCC3333CCCC3333CCCC3333CCCC3333"
    with patch("envault.rekey.decrypt", return_value=b"plain"):
        with patch("envault.rekey.encrypt", return_value=b"NEWENC"):
            rekey(vault_with_file, [new_fp])

    vault = Vault(vault_with_file)
    assert vault.get_recipients() == [new_fp]


def test_rekey_records_audit_event(vault_with_file: Path) -> None:
    from envault.audit import read_events

    new_fp = "DDDD4444DDDD4444DDDD4444DDDD4444DDDD4444"
    with patch("envault.rekey.decrypt", return_value=b"plain"):
        with patch("envault.rekey.encrypt", return_value=b"NEWENC"):
            rekey(vault_with_file, [new_fp])

    events = read_events(vault_with_file)
    assert any(e["event"] == "rekey" for e in events)
