"""Register the access command group with the main envault CLI.

Import this module in envault/cli.py to attach the access sub-commands::

    from envault.cli_access_register import register
    register(cli)
"""

from __future__ import annotations

import click

from envault.cli_access import access_group


def register(cli: click.Group) -> None:
    """Attach the ``access`` command group to *cli*."""
    cli.add_command(access_group, name="access")
