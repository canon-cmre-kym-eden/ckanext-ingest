from __future__ import annotations

import logging

import click


from .strategy import strategies

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
    for s in strategies:
        click.secho(f"{s.name()} [{s.__module__}:{s.__name__}]:", bold=True)

        for mime in sorted(s.mimetypes):
            click.echo(f"\t{mime}")
