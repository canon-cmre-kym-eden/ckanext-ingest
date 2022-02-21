from __future__ import annotations

import click
import logging
from . import strategy
logger = logging.getLogger(__name__)


def get_commnads():
    return [ingest]


@click.group(short_help="Ingestion management")
def ingest():
    pass


@ingest.command()
def supported():
    for s in strategy.strategies:
        click.secho(f"{s.name()} [{s.__module__}:{s.__name__}]:", bold=True)

        for mime in sorted(s.mimetypes):
            click.echo(f"\t{mime}")
