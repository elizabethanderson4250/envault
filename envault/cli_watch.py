"""CLI commands for the envault watch feature."""

from __future__ import annotations

from pathlib import Path

import click

from envault.audit import record_event
from envault.vault import Vault
from envault.watch import WatchError, WatchEvent, watch


@click.group("watch")
def watch_group() -> None:
    """Watch a .env file and re-lock on changes."""


@watch_group.command("start")
@click.argument("vault_dir", default=".", type=click.Path(file_okay=False))
@click.option(
    "--env-file",
    default=".env",
    show_default=True,
    help="Name of the .env file inside VAULT_DIR.",
)
@click.option(
    "--interval",
    default=2.0,
    show_default=True,
    type=float,
    help="Polling interval in seconds.",
)
def watch_start(vault_dir: str, env_file: str, interval: float) -> None:
    """Watch ENV_FILE and re-lock the vault whenever it changes."""
    base = Path(vault_dir).resolve()
    env_path = base / env_file
    vault = Vault(base)

    click.echo(f"Watching {env_path} (interval={interval}s) — press Ctrl+C to stop.")

    def _on_change(event: WatchEvent) -> None:
        if not event.new_hash:
            click.echo(f"[watch] {env_path.name} was removed — skipping lock.")
            return
        click.echo(f"[watch] Change detected in {env_path.name}, re-locking …")
        try:
            recipients = vault.get_recipients()
            if not recipients:
                click.echo("[watch] No recipients configured — skipping lock.", err=True)
                return
            vault.lock(env_path)
            record_event(base, "watch_relock", {"file": env_path.name})
            click.echo("[watch] Vault locked successfully.")
        except Exception as exc:  # noqa: BLE001
            click.echo(f"[watch] Lock failed: {exc}", err=True)

    try:
        watch(env_path, _on_change, interval=interval)
    except WatchError as exc:
        raise click.ClickException(str(exc)) from exc
    except KeyboardInterrupt:
        click.echo("\n[watch] Stopped.")
