"""Unit tests for envault.crypto (GPG operations)."""

import pytest
from unittest.mock import patch, MagicMock

from envault.crypto import encrypt, decrypt, list_secret_keys, GPGError


SAMPLE_CIPHERTEXT = b"-----BEGIN PGP MESSAGE-----\nfakedata\n-----END PGP MESSAGE-----\n"
SAMPLE_PLAINTEXT = b"SECRET=hunter2\nAPI_KEY=abc123\n"


def _make_proc(returncode=0, stdout=b"", stderr=b""):
    proc = MagicMock()
    proc.returncode = returncode
    proc.stdout = stdout
    proc.stderr = stderr
    return proc


@patch("envault.crypto.shutil.which", return_value="/usr/bin/gpg2")
@patch("envault.crypto.subprocess.run")
def test_encrypt_success(mock_run, mock_which):
    mock_run.return_value = _make_proc(stdout=SAMPLE_CIPHERTEXT)
    result = encrypt(SAMPLE_PLAINTEXT, recipients=["alice@example.com"])
    assert result == SAMPLE_CIPHERTEXT
    args = mock_run.call_args[0][0]
    assert "--encrypt" in args
    assert "--recipient" in args
    assert "alice@example.com" in args


@patch("envault.crypto.shutil.which", return_value="/usr/bin/gpg2")
@patch("envault.crypto.subprocess.run")
def test_encrypt_failure_raises(mock_run, mock_which):
    mock_run.return_value = _make_proc(returncode=2, stderr=b"key not found")
    with pytest.raises(GPGError, match="key not found"):
        encrypt(SAMPLE_PLAINTEXT, recipients=["nobody@example.com"])


def test_encrypt_no_recipients_raises():
    with pytest.raises(GPGError, match="At least one recipient"):
        encrypt(SAMPLE_PLAINTEXT, recipients=[])


@patch("envault.crypto.shutil.which", return_value="/usr/bin/gpg2")
@patch("envault.crypto.subprocess.run")
def test_decrypt_success(mock_run, mock_which):
    mock_run.return_value = _make_proc(stdout=SAMPLE_PLAINTEXT)
    result = decrypt(SAMPLE_CIPHERTEXT)
    assert result == SAMPLE_PLAINTEXT


@patch("envault.crypto.shutil.which", return_value="/usr/bin/gpg2")
@patch("envault.crypto.subprocess.run")
def test_decrypt_failure_raises(mock_run, mock_which):
    mock_run.return_value = _make_proc(returncode=2, stderr=b"bad passphrase")
    with pytest.raises(GPGError, match="bad passphrase"):
        decrypt(SAMPLE_CIPHERTEXT)


@patch("envault.crypto.shutil.which", return_value=None)
def test_gpg_binary_missing(mock_which):
    with pytest.raises(GPGError, match="No GPG binary found"):
        encrypt(b"data", ["someone"])


@patch("envault.crypto.shutil.which", return_value="/usr/bin/gpg2")
@patch("envault.crypto.subprocess.run")
def test_list_secret_keys(mock_run, mock_which):
    colons_output = "fpr:::::::::ABCDEF1234567890::\n"
    mock_run.return_value = _make_proc(stdout=colons_output.encode())
    # Patch text=True behaviour — subprocess returns str when text=True
    mock_run.return_value.stdout = colons_output
    keys = list_secret_keys()
    assert "ABCDEF1234567890" in keys
