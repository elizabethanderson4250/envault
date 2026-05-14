"""GPG signing and signature verification for vault files."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from envault.crypto import _gpg_binary, GPGError


@dataclass
class SignatureInfo:
    fingerprint: str
    timestamp: str
    valid: bool
    signer_uid: str = ""


class SignError(Exception):
    """Raised when signing or verification fails."""


def sign_file(path: Path, fingerprint: str) -> Path:
    """Sign *path* with the given GPG key, writing a detached .sig file.

    Returns the path to the signature file.
    Raises SignError on failure.
    """
    sig_path = path.with_suffix(path.suffix + ".sig")
    gpg = _gpg_binary()
    cmd = [
        gpg, "--batch", "--yes",
        "--detach-sign", "--armor",
        "-u", fingerprint,
        "--output", str(sig_path),
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SignError(f"GPG signing failed: {result.stderr.strip()}")
    return sig_path


def verify_signature(path: Path, sig_path: Path | None = None) -> SignatureInfo:
    """Verify the detached GPG signature for *path*.

    If *sig_path* is None, defaults to ``<path>.sig``.
    Returns a :class:`SignatureInfo`.
    Raises SignError when the signature is missing or invalid.
    """
    if sig_path is None:
        sig_path = path.with_suffix(path.suffix + ".sig")
    if not sig_path.exists():
        raise SignError(f"Signature file not found: {sig_path}")

    gpg = _gpg_binary()
    cmd = [gpg, "--batch", "--status-fd", "1", "--verify", str(sig_path), str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    fingerprint = ""
    timestamp = ""
    uid = ""
    valid = False

    for line in result.stdout.splitlines():
        if line.startswith("[GNUPG:] GOODSIG"):
            valid = True
            parts = line.split(None, 3)
            if len(parts) >= 4:
                uid = parts[3]
        elif line.startswith("[GNUPG:] VALIDSIG"):
            parts = line.split()
            if len(parts) >= 3:
                fingerprint = parts[2]
            if len(parts) >= 5:
                timestamp = parts[4]

    if result.returncode != 0 and not valid:
        raise SignError(f"Signature verification failed: {result.stderr.strip()}")

    return SignatureInfo(fingerprint=fingerprint, timestamp=timestamp, valid=valid, signer_uid=uid)


def signature_path(path: Path) -> Path:
    """Return the conventional .sig path for *path*."""
    return path.with_suffix(path.suffix + ".sig")
