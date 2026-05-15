"""CLI commands for managing envault hooks."""
from __future__ import annotations

from pathlib import Path

import click

from envault.hook import HOOK_EVENTS, HookError, list_hooks, remove_hook, run_hook, set_hook


@click.group("hook")
def hook_group() -> None:
    """Manage pre/post operation hooks."""


@hook_group.command("set")
@click.argument("event", metavar="EVENT")
@click.argument("command", metavar="COMMAND")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
def set_cmd(event: str, command: str, vault_dir: str) -> None:
    """Register COMMAND to run on EVENT."""
    try:
        set_hook(Path(vault_dir), event, command)
        click.echo(f"Hook set: {event} -> {command}")
    except HookError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@hook_group.command("remove")
@click.argument("event", metavar="EVENT")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
def remove_cmd(event: str, vault_dir: str) -> None:
    """Remove the hook registered for EVENT."""
    try:
        removed = remove_hook(Path(vault_dir), event)
        if removed:
            click.echo(f"Hook removed for event '{event}'.")
        else:
            click.echo(f"No hook registered for event '{event}'.")
    except HookError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@hook_group.command("list")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
def list_cmd(vault_dir: str) -> None:
    """List all registered hooks."""
    try:
        hooks = list_hooks(Path(vault_dir))
    except HookError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if not hooks:
        click.echo("No hooks registered.")
        return
    for event in HOOK_EVENTS:
        if event in hooks:
            click.echo(f"  {event:<16} {hooks[event]}")


@hook_group.command("run")
@click.argument("event", metavar="EVENT")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
def run_cmd(event: str, vault_dir: str) -> None:
    """Manually trigger the hook for EVENT."""
    try:
        code = run_hook(Path(vault_dir), event)
        if code is None:
            click.echo(f"No hook registered for event '{event}'.")
        else:
            click.echo(f"Hook '{event}' completed (exit {code}).")
    except HookError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
