from __future__ import annotations

import cgi
import mimetypes

import magic
from werkzeug.datastructures import FileStorage

import ckan.plugins.toolkit as tk
from ckan.logic.schema import validator_args

from .. import artifact


def uploaded_file(value):
    if isinstance(value, FileStorage):
        return value

    if isinstance(value, cgi.FieldStorage):
        assert value.filename and value.file, "File must be specified"

        mime, _encoding = mimetypes.guess_type(value.filename)
        if not mime:
            mime = magic.from_buffer(value.file.read(1024), True)
            value.file.seek(0)

        return FileStorage(value.file, value.filename, content_type=mime)

    raise tk.Invalid(f"Unsupported upload type {type(value)}")


@validator_args
def import_records(
    not_missing,
    boolean_validator,
    default,
    convert_to_json_if_string,
    dict_only,
    one_of,
    natural_number_validator,
    ignore_missing,
):
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
    not_missing,
    default,
    natural_number_validator,
    ignore_missing,
    convert_to_json_if_string,
    dict_only,
):
    return {
        "source": [not_missing, uploaded_file],
        "extras": [default("{}"), convert_to_json_if_string, dict_only],
        # "start": [default(0), natural_number_validator],
        # "rows": [ignore_missing, natural_number_validator],
    }
