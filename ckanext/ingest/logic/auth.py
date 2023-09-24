from __future__ import annotations

from typing import Any

from ckan import authz, types


def ingest_use_ingest(context: types.Context, data_dict: dict[str, Any]):
    return authz.is_authorized("package_create", context, data_dict)


def ingest_import_records(context: types.Context, data_dict: dict[str, Any]):
    return authz.is_authorized("ingest_use_ingest", context, data_dict)


def ingest_extract_records(context: types.Context, data_dict: dict[str, Any]):
    return authz.is_authorized("ingest_use_ingest", context, data_dict)


def ingest_web_ui(context: types.Context, data_dict: dict[str, Any]):
    return authz.is_authorized("sysadmin", context, data_dict)
