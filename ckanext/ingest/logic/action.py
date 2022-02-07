from __future__ import annotations
import logging
from typing_extensions import TypedDict

import ckan.plugins.toolkit as tk
from ckan.logic import validate
import ckan.model as model

from ckanext.toolbelt.decorators import Collector
from werkzeug.datastructures import FileStorage

from . import schema
from .. import strategy

log = logging.getLogger(__name__)
action, get_actions = Collector("ingest").split()


class ImporDatasetPayload(TypedDict):
    source: FileStorage
    update_existing: bool


@action
@validate(schema.import_datasets)
def import_datasets(context, data_dict: ImporDatasetPayload):
    tk.check_access("ingest_import_datasets", context, data_dict)

    mime = data_dict["source"].content_type
    handler = strategy.get_handler(mime)
    if not handler:
        raise tk.ValidationError(
            {"source": [tk._("Unsupported MIMEType {mime}").format(mime=mime)]}
        )

    handler.parse(data_dict["source"].stream)

    ids = []
    for record in handler.records:
        if isinstance(record, strategy.PackageRecord):
            action = "package_create"
            if data_dict["update_existing"] and model.Package.get(record.data["name"]):
                action = "package_update"
        elif isinstance(record, strategy.ResourceRecord):
            action = "resource_create"
        else:
            assert False, f"Unexpected record: {record}"

        result = tk.get_action(action)({"user": context["user"]}, record.data)
        if action.startswith("package"):
            ids.append(result["id"])

    return ids
