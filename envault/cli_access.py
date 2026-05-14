"""CLI commands for managing per-recipient access levels."""

from __future__ import annotations

from pathlib import Path

import click

from envault.access import (
    AccessError,
    VALID_LEVELS,
    check_access,
    get_access,
    list_access,
    revoke_access,
    set_access,
)


@click.group("access")
def access_group() -> None:
    """Manage per-recipient access levels."""


@access_group.command("grant")
@click.argument("fingerprint")
@click.argument("level", type=click.Choice(list(VALID_LEVELS)))
@click.option("--vault-dir", default=".", show_default=True)
def grant_cmd(fingerprint: str, level: str, vault_dir: str) -> None:
    """Grant FINGERPRINT the given access LEVEL."""
    try:
        set_access(Path(vault_dir), fingerprint, level)
        click.echo(f"Granted {level} access to {fingerprint}.")
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@access_group.command("revoke")
@click.argument("fingerprint")
@click.option("--vault-dir", default=".", show_default=True)
def revoke_cmd(fingerprint: str, vault_dir: str) -> None:
    """Revoke access for FINGERPRINT."""
    try:
        removed = revoke_access(Path(vault_dir), fingerprint)
        if removed:
            click.echo(f"Access revoked for {fingerprint}.")
        else:
            click.echo(f"No entry found for {fingerprint}.")
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@access_group.command("show")
@click.argument("fingerprint")
@click.option("--vault-dir", default=".", show_default=True)
def show_cmd(fingerprint: str, vault_dir: str) -> None:
    """Show the access level for FINGERPRINT."""
    level = get_access(Path(vault_dir), fingerprint)
    if level is None:
        click.echo(f"{fingerprint}: no access entry.")
    else:
        click.echo(f"{fingerprint}: {level}")


@access_group.command("list")
@click.option("--vault-dir", default=".", show_default=True)
def list_cmd(vault_dir: str) -> None:
    """List all access entries."""
    entries = list_access(Path(vault_dir))
    if not entries:
        click.echo("No access entries.")
        return
    for entry in entries:
        click.echo(f"{entry['fingerprint']}  {entry['level']}")


@access_group.command("check")
@click.argument("fingerprint")
@click.argument("level", type=click.Choice(list(VALID_LEVELS)))
@click.option("--vault-dir", default=".", show_default=True)
def check_cmd(fingerprint: str, level: str, vault_dir: str) -> None:
    """Check whether FINGERPRINT has at least LEVEL access."""
    try:
        ok = check_access(Path(vault_dir), fingerprint, level)
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    if ok:
        click.echo(f"{fingerprint} has {level} access.")
    else:
        click.echo(f"{fingerprint} does NOT have {level} access.")
        raise SystemExit(1)
