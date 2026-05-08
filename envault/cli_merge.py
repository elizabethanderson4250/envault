"""CLI commands for merging .env files."""

from __future__ import annotations

from pathlib import Path

import click

from envault.merge import (
    ConflictStrategy,
    MergeError,
    format_merge_result,
    merge_env,
    write_merged,
)


@click.group(name="merge")
def merge_group() -> None:
    """Merge two .env files together."""


@merge_group.command(name="run")
@click.argument("base", type=click.Path(exists=True, path_type=Path))
@click.argument("incoming", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file (defaults to BASE).",
)
@click.option(
    "--strategy",
    "-s",
    type=click.Choice([s.value for s in ConflictStrategy], case_sensitive=False),
    default=ConflictStrategy.OURS.value,
    show_default=True,
    help="Conflict resolution strategy.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would change without writing.",
)
def merge_cmd(
    base: Path,
    incoming: Path,
    output: Path | None,
    strategy: str,
    dry_run: bool,
) -> None:
    """Merge INCOMING .env into BASE."""
    strat = ConflictStrategy(strategy)
    try:
        result = merge_env(base, incoming, strategy=strat)
    except MergeError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(format_merge_result(result))

    if result.has_conflicts:
        click.echo(
            f"\n⚠  {len(result.conflicts)} conflict(s) resolved using strategy '{strat.value}'."
        )

    if dry_run:
        click.echo("\n[dry-run] No files written.")
        return

    dest = output or base
    write_merged(result, dest)
    click.echo(f"\n✔ Merged result written to {dest}")
