from __future__ import annotations

import cgi
import mimetypes
from typing import Any
from ckan import types

import magic
from werkzeug.datastructures import FileStorage

import ckan.plugins.toolkit as tk
from ckan.logic.schema import validator_args

from ckanext.ingest import artifact


def uploaded_file(value: Any):
    if isinstance(value, FileStorage):
        return value

    if isinstance(value, cgi.FieldStorage):
        if not value.filename or not value.file:
            raise ValueError(value)

        mime, _encoding = mimetypes.guess_type(value.filename)
        if not mime:
            mime = magic.from_buffer(value.file.read(1024), True)
            value.file.seek(0)

        return FileStorage(value.file, value.filename, content_type=mime)

    msg = f"Unsupported upload type {type(value)}"
    raise tk.Invalid(msg)


@validator_args
def import_records(
    not_missing: types.Validator,
    boolean_validator: types.Validator,
    default: types.ValidatorFactory,
    convert_to_json_if_string: types.Validator,
    dict_only: types.Validator,
    one_of: types.ValidatorFactory,
    natural_number_validator: types.Validator,
    ignore_missing: types.Validator,
) -> types.Schema:
    return {
        "source": [not_missing, uploaded_file],
        "report": [default("stats"), one_of([t.name for t in artifact.Type])],
        "update_existing": [boolean_validator],
        "verbose": [boolean_validator],
        "defaults": [default("{}"), convert_to_json_if_string, dict_only],
        "overrides": [default("{}"), convert_to_json_if_string, dict_only],
        "start": [default(0), natural_number_validator],
        "rows": [ignore_missing, natural_number_validator],
        "extras": [default("{}"), convert_to_json_if_string, dict_only],
    }


@validator_args
def extract_records(
    not_missing: types.Validator,
    default: types.ValidatorFactory,
    convert_to_json_if_string: types.Validator,
    dict_only: types.Validator,
) -> types.Schema:
    return {
        "source": [not_missing, uploaded_file],
        "extras": [default("{}"), convert_to_json_if_string, dict_only],
    }
