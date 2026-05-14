"""CLI commands for managing vault key quotas."""

from __future__ import annotations

from pathlib import Path

import click

from envault.quota import (
    QuotaError,
    check_quota,
    delete_quota,
    format_quota,
    read_quota,
    set_quota,
)


@click.group("quota")
def quota_group() -> None:
    """Manage the maximum number of keys allowed in a vault."""


@quota_group.command("set")
@click.argument("vault_dir", type=click.Path(file_okay=False))
@click.argument("max_keys", type=int)
def set_cmd(vault_dir: str, max_keys: int) -> None:
    """Set the max-keys quota for VAULT_DIR."""
    try:
        set_quota(Path(vault_dir), max_keys)
        click.echo(f"Quota set: max {max_keys} keys.")
    except QuotaError as exc:
        raise click.ClickException(str(exc)) from exc


@quota_group.command("show")
@click.argument("vault_dir", type=click.Path(file_okay=False))
def show_cmd(vault_dir: str) -> None:
    """Show the current quota for VAULT_DIR."""
    try:
        max_keys = read_quota(Path(vault_dir))
        click.echo(f"Max keys: {max_keys}")
    except QuotaError as exc:
        raise click.ClickException(str(exc)) from exc


@quota_group.command("check")
@click.argument("vault_dir", type=click.Path(file_okay=False))
@click.argument("env_file", type=click.Path(dir_okay=False))
def check_cmd(vault_dir: str, env_file: str) -> None:
    """Check whether ENV_FILE exceeds the quota for VAULT_DIR."""
    try:
        result = check_quota(Path(vault_dir), Path(env_file))
        click.echo(format_quota(result))
        if result.exceeded:
            raise click.ClickException(
                f"Quota exceeded: {result.key_count} keys > limit of {result.max_keys}."
            )
    except QuotaError as exc:
        raise click.ClickException(str(exc)) from exc


@quota_group.command("clear")
@click.argument("vault_dir", type=click.Path(file_okay=False))
def clear_cmd(vault_dir: str) -> None:
    """Remove the quota setting for VAULT_DIR (resets to default)."""
    removed = delete_quota(Path(vault_dir))
    if removed:
        click.echo("Quota cleared.")
    else:
        click.echo("No quota was set.")
