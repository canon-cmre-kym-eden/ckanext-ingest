from __future__ import annotations

import magic
import mimetypes
import cgi

from werkzeug.datastructures import FileStorage

import ckan.plugins.toolkit as tk
from ckan.logic.schema import validator_args


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
def import_datasets(not_missing, boolean_validator):
    return {
        "source": [not_missing, uploaded_file],
        "update_existing": [boolean_validator],
    }
