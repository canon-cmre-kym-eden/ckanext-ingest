from __future__ import annotations

import ckan.plugins.toolkit as tk

CONFIG_ALLOWED = "ckanext.ingest.strategy.allowed"
CONFIG_DISABLED = "ckanext.ingest.strategy.disabled"

CONFIG_BASE_TEMPLATE = "ckanext.ingest.base_template"
CONFIG_ALLOW_TRANSFER = "ckanext.ingest.allow_resource_transfer"
CONFIG_NAME_MAPPING = "ckanext.ingest.strategy.name_mapping"


def allow_transfer() -> bool:
    return tk.config[CONFIG_ALLOW_TRANSFER]


def allowed_strategies() -> list[str]:
    return tk.config[CONFIG_ALLOWED]


def disabled_strategies() -> list[str]:
    return tk.config[CONFIG_DISABLED]


def base_template() -> str:
    return tk.config[CONFIG_BASE_TEMPLATE]


def name_mapping() -> dict[str, str]:
    return tk.config[CONFIG_NAME_MAPPING]
