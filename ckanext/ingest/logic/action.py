from __future__ import annotations

import logging
from typing import Any
from typing_extensions import TypedDict, Literal

import ckan.plugins.toolkit as tk
from ckan.logic import validate
import ckan.model as model

from ckanext.toolbelt.decorators import Collector

from . import schema
from .. import strategy, record

log = logging.getLogger(__name__)
action, get_actions = Collector("ingest").split()


class RecordDict(TypedDict):
    exists: bool
    type: Literal["package", "resource"]
    data: dict[str, Any]


@action
@validate(schema.extract_records)
def extract_records(context, data_dict) -> list[RecordDict]:
    tk.check_access("ingest_extract_records", context, data_dict)
    mime = data_dict["source"].content_type
    handler = strategy.get_handler(mime, data_dict["source"])
    if not handler:
        raise tk.ValidationError(
            {"source": [tk._("Unsupported MIMEType {mime}").format(mime=mime)]}
        )
    records: list[RecordDict] = []
    for r in handler.parse(data_dict["source"].stream):
        if isinstance(r, record.PackageRecord):
            exists = model.Package.get(r.data.get("name", "")) is not None
            type_ = "package"
        elif isinstance(r, record.ResourceRecord):
            exists = model.Resource.get(r.data.get("id", "")) is not None
            type_ = "resource"
        else:
            assert False, f"Unexpected record: {r}"

        records.append(
            {
                "type": type_,
                "exists": exists,
                "data": r.data,
            }
        )
    return records


@action
@validate(schema.import_records)
def import_records(context, data_dict):
    tk.check_access("ingest_import_records", context, data_dict)

    ids = []
    record: RecordDict
    for record in tk.get_action("ingest_extract_records")(context, data_dict):

        action = (
            record["type"]
            + "_"
            + (
                "update"
                if record["exists"] and data_dict["update_existing"]
                else "create"
            )
        )

        result = tk.get_action(action)({"user": context["user"]}, record["data"])
        if record["type"] == "package":
            ids.append(result["id"])

    return ids
