"""Tests for envault.sign."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envault.sign import sign_file, verify_signature, signature_path, SignError, SignatureInfo


def _proc(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
    p = MagicMock()
    p.returncode = returncode
    p.stdout = stdout
    p.stderr = stderr
    return p


def test_sign_file_success(tmp_path: Path) -> None:
    target = tmp_path / "vault.env.gpg"
    target.write_bytes(b"data")
    sig = tmp_path / "vault.env.gpg.sig"

    with patch("envault.sign.subprocess.run", return_value=_proc(0)) as mock_run:
        result = sign_file(target, "ABCDEF1234567890")

    assert result == sig
    args = mock_run.call_args[0][0]
    assert "--detach-sign" in args
    assert "ABCDEF1234567890" in args


def test_sign_file_failure_raises(tmp_path: Path) -> None:
    target = tmp_path / "vault.env.gpg"
    target.write_bytes(b"data")

    with patch("envault.sign.subprocess.run", return_value=_proc(1, stderr="no secret key")):
        with pytest.raises(SignError, match="no secret key"):
            sign_file(target, "DEADBEEF")


def test_verify_signature_valid(tmp_path: Path) -> None:
    target = tmp_path / "vault.env.gpg"
    target.write_bytes(b"data")
    sig = tmp_path / "vault.env.gpg.sig"
    sig.write_bytes(b"sig")

    stdout = (
        "[GNUPG:] GOODSIG ABCDEF Alice <alice@example.com>\n"
        "[GNUPG:] VALIDSIG ABCDEF1234567890ABCDEF1234567890ABCDEF12 2024-01-01 1704067200\n"
    )
    with patch("envault.sign.subprocess.run", return_value=_proc(0, stdout=stdout)):
        info = verify_signature(target)

    assert info.valid is True
    assert info.fingerprint == "ABCDEF1234567890ABCDEF1234567890ABCDEF12"
    assert info.signer_uid == "Alice <alice@example.com>"
    assert info.timestamp == "1704067200"


def test_verify_signature_missing_sig_raises(tmp_path: Path) -> None:
    target = tmp_path / "vault.env.gpg"
    target.write_bytes(b"data")

    with pytest.raises(SignError, match="Signature file not found"):
        verify_signature(target)


def test_verify_signature_invalid_raises(tmp_path: Path) -> None:
    target = tmp_path / "vault.env.gpg"
    target.write_bytes(b"data")
    sig = tmp_path / "vault.env.gpg.sig"
    sig.write_bytes(b"badsig")

    with patch("envault.sign.subprocess.run", return_value=_proc(1, stderr="BAD signature")):
        with pytest.raises(SignError, match="BAD signature"):
            verify_signature(target)


def test_verify_explicit_sig_path(tmp_path: Path) -> None:
    target = tmp_path / "vault.env.gpg"
    target.write_bytes(b"data")
    sig = tmp_path / "custom.sig"
    sig.write_bytes(b"sig")

    stdout = "[GNUPG:] GOODSIG AABBCC Bob <bob@example.com>\n"
    with patch("envault.sign.subprocess.run", return_value=_proc(0, stdout=stdout)):
        info = verify_signature(target, sig)

    assert info.valid is True


def test_signature_path_convention(tmp_path: Path) -> None:
    target = tmp_path / "vault.env.gpg"
    assert signature_path(target) == tmp_path / "vault.env.gpg.sig"
