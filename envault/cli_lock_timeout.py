"""CLI commands for managing vault lock timeouts."""

from __future__ import annotations

from pathlib import Path

import click

from .lock_timeout import (
    LockTimeoutError,
    set_timeout,
    read_timeout,
    is_expired,
    clear_timeout,
    format_timeout,
)


@click.group("lock-timeout", help="Manage automatic lock timeouts for a vault.")
def lock_timeout_group() -> None:  # pragma: no cover
    pass


@lock_timeout_group.command("set")
@click.argument("vault_dir", type=click.Path(file_okay=False))
@click.argument("minutes", type=int)
def set_cmd(vault_dir: str, minutes: int) -> None:
    """Set a lock timeout of MINUTES minutes for VAULT_DIR."""
    try:
        expires_at = set_timeout(Path(vault_dir), minutes)
        click.echo(f"Lock timeout set: vault will lock after {minutes} min (at {expires_at.isoformat()}).")
    except LockTimeoutError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@lock_timeout_group.command("show")
@click.argument("vault_dir", type=click.Path(file_okay=False))
def show_cmd(vault_dir: str) -> None:
    """Show the current lock timeout for VAULT_DIR."""
    try:
        data = read_timeout(Path(vault_dir))
    except LockTimeoutError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if data is None:
        click.echo("No lock timeout configured.")
    else:
        click.echo(format_timeout(data))


@lock_timeout_group.command("check")
@click.argument("vault_dir", type=click.Path(file_okay=False))
def check_cmd(vault_dir: str) -> None:
    """Exit 0 if timeout has NOT expired, 1 if it HAS expired."""
    if is_expired(Path(vault_dir)):
        click.echo("Timeout has expired — vault should be locked.", err=True)
        raise SystemExit(1)
    click.echo("Timeout has not expired.")


@lock_timeout_group.command("clear")
@click.argument("vault_dir", type=click.Path(file_okay=False))
def clear_cmd(vault_dir: str) -> None:
    """Remove the lock timeout for VAULT_DIR."""
    removed = clear_timeout(Path(vault_dir))
    if removed:
        click.echo("Lock timeout cleared.")
    else:
        click.echo("No lock timeout was set.")
