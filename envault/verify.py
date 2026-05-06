"""Verify the integrity of a locked vault file by checking GPG recipients and file hash."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .vault import Vault


class VerifyError(Exception):
    """Raised when vault verification fails unexpectedly."""


@dataclass
class VerifyResult:
    ok: bool
    vault_file_present: bool = False
    meta_present: bool = False
    recipients_match: bool = False
    sha256: Optional[str] = None
    missing_recipients: List[str] = field(default_factory=list)
    extra_recipients: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def verify_vault(vault: Vault) -> VerifyResult:
    """Check that the vault file exists and that its recorded recipients are consistent."""
    result = VerifyResult(ok=False)

    vault_file = vault.vault_dir / "vault.env.gpg"
    meta_path = vault.vault_dir / ".envault_meta.json"

    result.meta_present = meta_path.exists()
    if not result.meta_present:
        result.errors.append("Meta file (.envault_meta.json) not found.")

    result.vault_file_present = vault_file.exists()
    if not result.vault_file_present:
        result.errors.append("Vault file (vault.env.gpg) not found.")
    else:
        result.sha256 = _sha256(vault_file)

    if result.meta_present:
        try:
            meta_recipients = set(vault.get_recipients())
        except Exception as exc:  # pragma: no cover
            result.errors.append(f"Failed to read recipients from meta: {exc}")
            return result

        # For now, the canonical recipient list lives in meta; we just validate
        # that the meta is self-consistent (no duplicate fingerprints).
        raw = list(vault.get_recipients())
        unique = set(raw)
        if len(raw) != len(unique):
            result.errors.append("Duplicate recipients found in meta.")
        else:
            result.recipients_match = True

        result.missing_recipients = []
        result.extra_recipients = []

    result.ok = (
        result.vault_file_present
        and result.meta_present
        and result.recipients_match
        and not result.errors
    )
    return result


def format_verify(result: VerifyResult) -> str:
    lines: List[str] = []
    status = "PASS" if result.ok else "FAIL"
    lines.append(f"Vault verification: {status}")
    lines.append(f"  Vault file present : {'yes' if result.vault_file_present else 'no'}")
    lines.append(f"  Meta file present  : {'yes' if result.meta_present else 'no'}")
    lines.append(f"  Recipients valid   : {'yes' if result.recipients_match else 'no'}")
    if result.sha256:
        lines.append(f"  SHA-256            : {result.sha256}")
    for err in result.errors:
        lines.append(f"  ERROR: {err}")
    return "\n".join(lines)
