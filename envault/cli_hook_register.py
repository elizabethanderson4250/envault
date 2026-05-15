"""Register hook commands with the main CLI."""
from __future__ import annotations

from envault.cli_hook import hook_group


def register(cli) -> None:  # noqa: ANN001
    """Attach the hook command group to *cli*."""
    cli.add_command(hook_group, name="hook")
