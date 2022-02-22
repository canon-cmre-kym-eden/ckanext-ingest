from __future__ import annotations
import mimetypes

import click
import logging
from werkzeug.datastructures import FileStorage
import ckan.plugins.toolkit as tk
from . import strategy, artifact

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


@ingest.command()
@click.argument("source", type=click.File("rb"))
@click.option("-r", "--report", default="tmp", type=click.Choice([t.name for t in artifact.Type]))
def process(source, report):
    user = tk.get_action("get_site_user")({"ignore_auth": True}, {})
    mime, _enc = mimetypes.guess_type(source.name)

    result = tk.get_action("ingest_import_records")(
        {"user": user["name"], "with_progressbar": True},
        {"source": FileStorage(source, content_type=mime), "report": report}
    )
    click.echo(result)
