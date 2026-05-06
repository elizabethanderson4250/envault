"""CLI commands for viewing vault operation history."""

from __future__ import annotations

from pathlib import Path

import click

from envault.history import filter_events, format_history, HISTORY_EVENTS


@click.group("history")
def history_group() -> None:
    """Commands for inspecting vault operation history."""


@history_group.command("show")
@click.argument("vault_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--type",
    "event_type",
    multiple=True,
    type=click.Choice(sorted(HISTORY_EVENTS)),
    help="Filter by event type (repeatable).",
)
@click.option(
    "--limit",
    default=None,
    type=int,
    show_default=True,
    help="Maximum number of events to show.",
)
def history_show(
    vault_dir: Path,
    event_type: tuple,
    limit: int | None,
) -> None:
    """Show the operation history for VAULT_DIR."""
    types = list(event_type) if event_type else None
    events = filter_events(vault_dir, event_types=types, limit=limit)
    click.echo(format_history(events))
