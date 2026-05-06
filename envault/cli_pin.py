"""CLI commands for pin management."""

from __future__ import annotations

from pathlib import Path

import click

from envault.pin import (
    PinError,
    create_pin,
    delete_pin,
    format_pin,
    read_pin,
    verify_pin,
)


@click.group("pin")
def pin_group() -> None:
    """Pin the vault to a specific .env file checksum."""


@pin_group.command("set")
@click.argument("vault_dir", type=click.Path(file_okay=False))
@click.argument("env_file", type=click.Path(dir_okay=False))
def set_pin(vault_dir: str, env_file: str) -> None:
    """Create or update the pin for ENV_FILE inside VAULT_DIR."""
    try:
        record = create_pin(Path(vault_dir), Path(env_file))
        click.echo("Pin created.")
        click.echo(format_pin(record))
    except PinError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@pin_group.command("verify")
@click.argument("vault_dir", type=click.Path(file_okay=False))
@click.argument("env_file", type=click.Path(dir_okay=False))
def verify_pin_cmd(vault_dir: str, env_file: str) -> None:
    """Verify ENV_FILE matches the stored pin in VAULT_DIR."""
    try:
        ok = verify_pin(Path(vault_dir), Path(env_file))
    except PinError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if ok:
        click.echo("OK: file matches pin.")
    else:
        click.echo("MISMATCH: file does not match pin.", err=True)
        raise SystemExit(1)


@pin_group.command("show")
@click.argument("vault_dir", type=click.Path(file_okay=False))
def show_pin(vault_dir: str) -> None:
    """Display the current pin for VAULT_DIR."""
    record = read_pin(Path(vault_dir))
    if record is None:
        click.echo("No pin set.")
    else:
        click.echo(format_pin(record))


@pin_group.command("delete")
@click.argument("vault_dir", type=click.Path(file_okay=False))
def delete_pin_cmd(vault_dir: str) -> None:
    """Remove the pin from VAULT_DIR."""
    removed = delete_pin(Path(vault_dir))
    if removed:
        click.echo("Pin deleted.")
    else:
        click.echo("No pin to delete.")
