"""CLI commands for managing envault notifications."""
from __future__ import annotations

from pathlib import Path

import click

from .notify import NotifyConfig, NotifyError, load_config, save_config


@click.group("notify")
def notify_group() -> None:
    """Configure event notifications."""


@notify_group.command("set")
@click.option("--channel", required=True, type=click.Choice(["stdout", "exec", "file"]),
              help="Notification channel.")
@click.option("--target", default="", show_default=True,
              help="Command or file path (required for exec/file channels).")
@click.option("--events", default="", show_default=True,
              help="Comma-separated event names to subscribe to (empty = all).")
@click.argument("vault_dir", default=".", type=click.Path())
def set_cmd(channel: str, target: str, events: str, vault_dir: str) -> None:
    """Configure a notification channel for this vault."""
    event_list = [e.strip() for e in events.split(",") if e.strip()]
    config = NotifyConfig(channel=channel, target=target, events=event_list)
    try:
        save_config(Path(vault_dir), config)
        click.echo(f"Notification channel '{channel}' configured.")
    except NotifyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@notify_group.command("show")
@click.argument("vault_dir", default=".", type=click.Path())
def show_cmd(vault_dir: str) -> None:
    """Show current notification configuration."""
    try:
        config = load_config(Path(vault_dir))
    except NotifyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if config is None:
        click.echo("No notification configuration found.")
        return

    click.echo(f"Channel : {config.channel}")
    click.echo(f"Target  : {config.target or '(none)'}")
    click.echo(f"Events  : {', '.join(config.events) if config.events else '(all)'}")


@notify_group.command("clear")
@click.argument("vault_dir", default=".", type=click.Path())
def clear_cmd(vault_dir: str) -> None:
    """Remove notification configuration."""
    from pathlib import Path as _Path
    cfg_path = _Path(vault_dir) / ".envault" / "notify.json"
    if cfg_path.exists():
        cfg_path.unlink()
        click.echo("Notification configuration removed.")
    else:
        click.echo("No notification configuration to remove.")
