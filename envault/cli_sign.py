"""CLI commands for signing and verifying vault files."""
from __future__ import annotations

from pathlib import Path

import click

from envault.sign import sign_file, verify_signature, SignError
from envault.audit import record_event


@click.group("sign")
def sign_group() -> None:
    """Sign and verify vault file signatures."""


@sign_group.command("file")
@click.argument("vault_dir", type=click.Path(exists=True, file_okay=False))
@click.argument("target", type=click.Path(exists=True, dir_okay=False))
@click.option("--fingerprint", "-k", required=True, help="GPG key fingerprint to sign with.")
def sign_cmd(vault_dir: str, target: str, fingerprint: str) -> None:
    """Sign TARGET file with the given GPG key fingerprint."""
    target_path = Path(target)
    try:
        sig = sign_file(target_path, fingerprint)
        record_event(
            Path(vault_dir),
            "sign",
            {"file": target_path.name, "fingerprint": fingerprint},
        )
        click.echo(f"Signed: {sig}")
    except SignError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@sign_group.command("verify")
@click.argument("vault_dir", type=click.Path(exists=True, file_okay=False))
@click.argument("target", type=click.Path(exists=True, dir_okay=False))
@click.option("--sig", "sig_path", default=None, help="Path to .sig file (default: <target>.sig).")
def verify_cmd(vault_dir: str, target: str, sig_path: str | None) -> None:
    """Verify the GPG signature of TARGET."""
    target_path = Path(target)
    sp = Path(sig_path) if sig_path else None
    try:
        info = verify_signature(target_path, sp)
        status = "VALID" if info.valid else "INVALID"
        click.echo(f"Signature: {status}")
        if info.fingerprint:
            click.echo(f"Fingerprint: {info.fingerprint}")
        if info.signer_uid:
            click.echo(f"Signer: {info.signer_uid}")
        if info.timestamp:
            click.echo(f"Timestamp: {info.timestamp}")
        record_event(
            Path(vault_dir),
            "verify_signature",
            {"file": target_path.name, "valid": info.valid, "fingerprint": info.fingerprint},
        )
    except SignError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
