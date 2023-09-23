from __future__ import annotations

import itertools
import logging
import mimetypes
from typing import Any, Iterable

import ckan.plugins.toolkit as tk
from ckan import types
from ckan.logic import validate

from ckanext.ingest import shared
from ckanext.ingest.artifact import make_artifacts

from . import schema

log = logging.getLogger(__name__)


@validate(schema.extract_records)
def ingest_extract_records(
    context: types.Context,
    data_dict: dict[str, Any],
) -> list[dict[str, Any]]:
    tk.check_access("ingest_extract_records", context, data_dict)
    records = _iter_records(data_dict)

    return [r.data for r in records]


@validate(schema.import_records)
def ingest_import_records(context: types.Context, data_dict: dict[str, Any]):
    tk.check_access("ingest_import_records", context, data_dict)

    start = data_dict["skip"]
    stop = data_dict.get("take")
    if stop is not None:
        stop += start

    artifacts = make_artifacts(data_dict["report"])
    records = _iter_records(data_dict)

    for record in itertools.islice(records, start, stop):
        record.fill(data_dict["defaults"], data_dict["overrides"])
        try:
            result = record.ingest(tk.fresh_context(context))
        except tk.ValidationError as e:
            artifacts.fail({"error": e.error_dict, "source": record.raw})
        except tk.ObjectNotFound as e:
            artifacts.fail(
                {
                    "error": e.message or "Package does not exists",
                    "source": record.raw,
                },
            )

        else:
            artifacts.success({"result": result})

    return artifacts.collect()


def _iter_records(data_dict: dict[str, Any]) -> Iterable[shared.Record]:
    """Produce iterable over all extracted records.

    When `strategy` is present in `data_dict`, it explicitly defines extraction
    strategy. If `strategy` is missing, the most suitable strategy is chosen
    depending on `source`'s mimetype.

    """
    source: shared.Storage = data_dict["source"]

    if "strategy" in data_dict:
        parser = shared.strategies[data_dict["strategy"]]()

    else:
        mime = None

        if source.filename:
            mime, _encoding = mimetypes.guess_type(source.filename)

        if not mime:
            mime = data_dict["source"].content_type

        parser = shared.get_handler_for_mimetype(mime, data_dict["source"])

        if not parser:
            raise tk.ValidationError(
                {"source": [tk._("Unsupported MIMEType {mime}").format(mime=mime)]},
            )

    return parser.extract(data_dict["source"], data_dict["options"])
