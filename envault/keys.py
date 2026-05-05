"""Key discovery and validation utilities for envault."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import List, Optional

from envault.crypto import GPGError, _gpg_binary

FINGERPRINT_RE = re.compile(r"^[0-9A-Fa-f]{16,40}$")


@dataclass
class KeyInfo:
    fingerprint: str
    uids: List[str]
    is_secret: bool = False

    def short_id(self) -> str:
        """Return the last 16 characters of the fingerprint."""
        return self.fingerprint[-16:]

    def primary_uid(self) -> str:
        return self.uids[0] if self.uids else "<unknown>"


def is_valid_fingerprint(value: str) -> bool:
    """Return True if *value* looks like a valid GPG fingerprint."""
    return bool(FINGERPRINT_RE.match(value.strip()))


def lookup_key(fingerprint: str) -> Optional[KeyInfo]:
    """Look up a public key by fingerprint.  Returns None if not found."""
    if not is_valid_fingerprint(fingerprint):
        raise ValueError(f"Invalid fingerprint format: {fingerprint!r}")

    gpg = _gpg_binary()
    cmd = [
        gpg,
        "--batch",
        "--with-colons",
        "--fingerprint",
        fingerprint,
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as exc:
        if "No public key" in exc.stderr or exc.returncode == 2:
            return None
        raise GPGError(f"GPG lookup failed: {exc.stderr.strip()}") from exc

    uids: List[str] = []
    resolved_fp: Optional[str] = None

    for line in result.stdout.splitlines():
        parts = line.split(":")
        if parts[0] == "fpr" and not resolved_fp:
            resolved_fp = parts[9]
        elif parts[0] == "uid":
            uids.append(parts[9])

    if not resolved_fp:
        return None

    return KeyInfo(fingerprint=resolved_fp, uids=uids)


def list_public_keys() -> List[KeyInfo]:
    """Return all public keys available in the local GPG keyring."""
    gpg = _gpg_binary()
    result = subprocess.run(
        [gpg, "--batch", "--with-colons", "--list-keys"],
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 2):
        raise GPGError(f"GPG list-keys failed: {result.stderr.strip()}")

    keys: List[KeyInfo] = []
    current_fp: Optional[str] = None
    current_uids: List[str] = []

    for line in result.stdout.splitlines():
        parts = line.split(":")
        if parts[0] == "pub":
            if current_fp:
                keys.append(KeyInfo(fingerprint=current_fp, uids=current_uids))
            current_fp = None
            current_uids = []
        elif parts[0] == "fpr":
            current_fp = parts[9]
        elif parts[0] == "uid":
            current_uids.append(parts[9])

    if current_fp:
        keys.append(KeyInfo(fingerprint=current_fp, uids=current_uids))

    return keys
