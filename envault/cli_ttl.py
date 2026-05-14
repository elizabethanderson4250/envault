"""CLI commands for managing decrypted-file TTL enforcement."""
from __future__ import annotations

from pathlib import Path

import click

from .ttl import TTLError, set_ttl, read_ttl, is_expired, clear_ttl, remaining_seconds


@click.group("ttl", help="Manage TTL for decrypted .env files.")
def ttl_group() -> None:
    pass


@ttl_group.command("set")
@click.argument("vault_dir", type=click.Path(file_okay=False))
@click.argument("seconds", type=int)
def set_cmd(vault_dir: str, seconds: int) -> None:
    """Set a TTL of SECONDS for the decrypted .env in VAULT_DIR."""
    try:
        expires_at = set_ttl(Path(vault_dir), seconds)
        click.echo(f"TTL set: expires at {expires_at.isoformat()}")
    except TTLError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@ttl_group.command("show")
@click.argument("vault_dir", type=click.Path(file_okay=False))
def show_cmd(vault_dir: str) -> None:
    """Show the current TTL record for VAULT_DIR."""
    record = read_ttl(Path(vault_dir))
    if record is None:
        click.echo("No TTL set.")
        return
    secs = remaining_seconds(Path(vault_dir))
    status = "EXPIRED" if (secs is not None and secs <= 0) else f"{secs:.0f}s remaining"
    click.echo(f"Expires at : {record['expires_at']}")
    click.echo(f"Status     : {status}")


@ttl_group.command("check")
@click.argument("vault_dir", type=click.Path(file_okay=False))
def check_cmd(vault_dir: str) -> None:
    """Exit non-zero if the TTL has expired (or no TTL is set)."""
    record = read_ttl(Path(vault_dir))
    if record is None:
        click.echo("No TTL set.", err=True)
        raise SystemExit(1)
    if is_expired(Path(vault_dir)):
        click.echo("TTL has expired.", err=True)
        raise SystemExit(1)
    secs = remaining_seconds(Path(vault_dir))
    click.echo(f"TTL valid — {secs:.0f}s remaining.")


@ttl_group.command("clear")
@click.argument("vault_dir", type=click.Path(file_okay=False))
def clear_cmd(vault_dir: str) -> None:
    """Remove the TTL record for VAULT_DIR."""
    removed = clear_ttl(Path(vault_dir))
    if removed:
        click.echo("TTL cleared.")
    else:
        click.echo("No TTL record found.")
