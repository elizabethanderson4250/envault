"""GPG-based encryption and decryption utilities for envault."""

import subprocess
import shutil
from typing import List, Optional


class GPGError(Exception):
    """Raised when a GPG operation fails."""
    pass


def _gpg_binary() -> str:
    """Return the path to the gpg binary, preferring gpg2."""
    for binary in ("gpg2", "gpg"):
        if shutil.which(binary):
            return binary
    raise GPGError("No GPG binary found. Please install GnuPG.")


def encrypt(plaintext: bytes, recipients: List[str]) -> bytes:
    """
    Encrypt *plaintext* for one or more GPG *recipients* (key IDs or emails).
    Returns the ASCII-armored ciphertext as bytes.
    """
    if not recipients:
        raise GPGError("At least one recipient is required for encryption.")

    cmd = [_gpg_binary(), "--batch", "--yes", "--armor", "--encrypt"]
    for recipient in recipients:
        cmd += ["--recipient", recipient]

    result = subprocess.run(
        cmd,
        input=plaintext,
        capture_output=True,
    )
    if result.returncode != 0:
        raise GPGError(f"GPG encryption failed: {result.stderr.decode().strip()}")
    return result.stdout


def decrypt(ciphertext: bytes, passphrase: Optional[str] = None) -> bytes:
    """
    Decrypt GPG-encrypted *ciphertext*.
    If *passphrase* is provided it is passed via stdin (for symmetric/loopback).
    Returns the plaintext as bytes.
    """
    cmd = [
        _gpg_binary(),
        "--batch",
        "--yes",
        "--decrypt",
    ]
    if passphrase is not None:
        cmd += ["--pinentry-mode", "loopback", "--passphrase-fd", "0"]
        input_data = passphrase.encode() + b"\n" + ciphertext
    else:
        input_data = ciphertext

    result = subprocess.run(
        cmd,
        input=input_data,
        capture_output=True,
    )
    if result.returncode != 0:
        raise GPGError(f"GPG decryption failed: {result.stderr.decode().strip()}")
    return result.stdout


def list_secret_keys() -> List[str]:
    """Return a list of fingerprints for available secret keys."""
    result = subprocess.run(
        [_gpg_binary(), "--list-secret-keys", "--with-colons"],
        capture_output=True,
        text=True,
    )
    fingerprints = []
    for line in result.stdout.splitlines():
        if line.startswith("fpr:"):
            parts = line.split(":")
            if len(parts) > 9 and parts[9]:
                fingerprints.append(parts[9])
    return fingerprints
