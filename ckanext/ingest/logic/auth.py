from __future__ import annotations

import ckan.plugins.toolkit as tk

from ckanext.toolbelt.decorators import Collector

auth, get_auth_functions = Collector("ingest").split()


@auth
def import_records(context, data_dict):
    return tk.check_access("package_create", context, data_dict)


@auth
def extract_records(context, data_dict):
    return tk.check_access("package_create", context, data_dict)


@auth
def web_ui(context, data_dict):
    return tk.check_access("package_create", context, data_dict)
