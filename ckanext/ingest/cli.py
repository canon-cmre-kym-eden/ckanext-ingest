from __future__ import annotations

import logging
import mimetypes
from typing import IO, Optional

import click
from werkzeug.datastructures import FileStorage

import ckan.plugins.toolkit as tk

from . import artifact, strategy

logger = logging.getLogger(__name__)


def get_commnads():
    return [ingest]


@click.group(short_help="Ingestion management")
def ingest():
    pass


@ingest.command()
def supported():
    """List supported input strategies and corresponding mimetypes."""
    for s in strategy.strategies:
        click.secho(f"{s.name()} [{s.__module__}:{s.__name__}]:", bold=True)

        for mime in sorted(s.mimetypes):
            click.echo(f"\t{mime}")


@ingest.command()
@click.argument("source", type=click.File("rb"))
@click.option(
    "-r",
    "--report",
    default="tmp",
    type=click.Choice([t.name for t in artifact.Type]),
    help="The form of processing report",
)
@click.option("--start", type=int, default=0, help="Number of items to skip")
@click.option("--rows", type=int, help="Number of items to process(all by default)")
@click.option(
    "-d",
    "--defaults",
    type=lambda v: v.split("=", 1),
    multiple=True,
    metavar="KEY=VALUE",
    help="Default properties that are used when data is missing from source",
)
@click.option(
    "-o",
    "--overrides",
    type=lambda v: v.split("=", 1),
    multiple=True,
    metavar="KEY=VALUE",
    help="Properties that are used {} of the data from source".format(
        click.style("instead", bold=True)
    ),
)
@click.option(
    "-e",
    "--extras",
    type=lambda v: v.split("=", 1),
    multiple=True,
    metavar="KEY=VALUE",
    help="Extra properties that are sent to the source parser.",
)
@click.pass_context
def process(
    ctx: click.Context,
    source: IO[bytes],
    report: str,
    start: int,
    rows: Optional[int],
    defaults: tuple[list[str]],
    overrides: tuple[list[str]],
    extras: tuple[list[str]],
):
    """Ingest data from source into CKAN."""
    user = tk.get_action("get_site_user")({"ignore_auth": True}, {})
    mime, _enc = mimetypes.guess_type(source.name)

    with ctx.meta["flask_app"].test_request_context():
        tk.g.user = user["name"]

        result = tk.get_action("ingest_import_records")(
            {"user": user["name"]},
            {
                "source": FileStorage(source, content_type=mime),
                "report": report,
                "start": start,
                "rows": rows,
                "update_existing": True,
                "defaults": dict(pair for pair in defaults if len(pair) == 2),
                "overrides": dict(pair for pair in overrides if len(pair) == 2),
                "extras": dict(pair for pair in extras if len(pair) == 2),
            },
        )
    click.echo(result)
