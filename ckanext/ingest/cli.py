from __future__ import annotations

import logging
import pydoc
import textwrap

import click

from .shared import strategies

logger = logging.getLogger(__name__)

__all__ = [
    "ingest",
]


@click.group(short_help="Ingestion management")
def ingest():
    pass


@ingest.group()
def strategy():
    pass


@strategy.command("list")
def list_strategies():
    """List supported input strategies and corresponding mimetypes."""
    for name, strategy in strategies.items():
        click.secho(f"{name} [{strategy.__module__}:{strategy.__name__}]:", bold=True)
        click.echo(textwrap.indent(pydoc.getdoc(strategy) + "\n", "\t"))
