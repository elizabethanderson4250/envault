"""cli_prune.py — CLI commands for pruning stale keys from a .env file."""
from __future__ import annotations

from pathlib import Path

import click

from .prune import PruneError, format_prune, prune_keys


@click.group("prune")
def prune_group() -> None:  # pragma: no cover
    """Remove unwanted keys from a .env file."""


@prune_group.command("run")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.argument("keys", nargs=-1, required=True)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview changes without modifying the file.",
)
def prune_cmd(env_file: Path, keys: tuple[str, ...], dry_run: bool) -> None:
    """Remove KEYS from ENV_FILE.

    Example:

        envault prune run .env OLD_KEY DEPRECATED_VAR
    """
    try:
        result = prune_keys(env_file, list(keys), dry_run=dry_run)
    except PruneError as exc:
        raise click.ClickException(str(exc)) from exc

    summary = format_prune(result)
    if dry_run and result.changed:
        click.echo("[dry-run] " + summary)
    else:
        click.echo(summary)
