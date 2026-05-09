"""CLI commands for vault backup and restore."""

from __future__ import annotations

from pathlib import Path

import click

from .backup import BackupError, create_backup, delete_backup, list_backups, restore_backup


@click.group("backup")
def backup_group() -> None:
    """Manage vault backups."""


@backup_group.command("create")
@click.argument("vault_dir", default=".", type=click.Path(file_okay=False))
def create_cmd(vault_dir: str) -> None:
    """Create a timestamped backup of the current vault."""
    try:
        dest = create_backup(Path(vault_dir))
        click.echo(f"Backup created: {dest}")
    except BackupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@backup_group.command("list")
@click.argument("vault_dir", default=".", type=click.Path(file_okay=False))
def list_cmd(vault_dir: str) -> None:
    """List available backups (newest first)."""
    backups = list_backups(Path(vault_dir))
    if not backups:
        click.echo("No backups found.")
        return
    for b in backups:
        click.echo(b.name)


@backup_group.command("restore")
@click.argument("vault_dir", type=click.Path(file_okay=False))
@click.argument("backup_name")
def restore_cmd(vault_dir: str, backup_name: str) -> None:
    """Restore a backup by its timestamp name."""
    from .backup import BACKUP_DIR

    vdir = Path(vault_dir)
    backup_path = vdir / BACKUP_DIR / backup_name
    try:
        restore_backup(vdir, backup_path)
        click.echo(f"Restored from backup: {backup_name}")
    except BackupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@backup_group.command("delete")
@click.argument("vault_dir", type=click.Path(file_okay=False))
@click.argument("backup_name")
@click.confirmation_option(prompt="Delete this backup?")
def delete_cmd(vault_dir: str, backup_name: str) -> None:
    """Delete a backup by its timestamp name."""
    from .backup import BACKUP_DIR

    backup_path = Path(vault_dir) / BACKUP_DIR / backup_name
    try:
        delete_backup(backup_path)
        click.echo(f"Deleted backup: {backup_name}")
    except BackupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
