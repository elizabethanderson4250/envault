"""CLI commands for vault secret expiry management."""

from __future__ import annotations

from pathlib import Path

import click

from envault.expire import (
    ExpiryError,
    delete_expiry,
    format_expiry,
    is_expired,
    set_expiry,
)


@click.group("expire", help="Manage expiry for vault secrets.")
def expire_group() -> None:
    pass


@expire_group.command("set")
@click.argument("vault_dir", type=click.Path(file_okay=False))
@click.option("--days", required=True, type=int, help="Number of days until expiry.")
def set_cmd(vault_dir: str, days: int) -> None:
    """Set an expiry date DAYS from now for the vault at VAULT_DIR."""
    try:
        expires_at = set_expiry(Path(vault_dir), days)
        click.echo(f"Expiry set: {expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    except ExpiryError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@expire_group.command("show")
@click.argument("vault_dir", type=click.Path(file_okay=False))
def show_cmd(vault_dir: str) -> None:
    """Show the current expiry status for the vault at VAULT_DIR."""
    try:
        click.echo(format_expiry(Path(vault_dir)))
    except ExpiryError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@expire_group.command("check")
@click.argument("vault_dir", type=click.Path(file_okay=False))
def check_cmd(vault_dir: str) -> None:
    """Exit with code 1 if the vault at VAULT_DIR has expired."""
    try:
        if is_expired(Path(vault_dir)):
            click.echo("Vault has EXPIRED.", err=True)
            raise SystemExit(1)
        click.echo("Vault is valid (not expired).")
    except ExpiryError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@expire_group.command("clear")
@click.argument("vault_dir", type=click.Path(file_okay=False))
def clear_cmd(vault_dir: str) -> None:
    """Remove the expiry setting from the vault at VAULT_DIR."""
    removed = delete_expiry(Path(vault_dir))
    if removed:
        click.echo("Expiry cleared.")
    else:
        click.echo("No expiry was set.")
