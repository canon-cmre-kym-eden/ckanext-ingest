from __future__ import annotations

import ckan.plugins.toolkit as tk

CONFIG_BASE_TEMPLATE = "ckanext.ingest.base_template"
DEFAULT_BASE_TEMPLATE = "page.html"


def get_base_template():
    """Return parent template for ingest page."""
    return tk.config.get(CONFIG_BASE_TEMPLATE, DEFAULT_BASE_TEMPLATE)
