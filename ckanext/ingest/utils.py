from __future__ import annotations
import json
import dataclasses
from typing import Any, NamedTuple, Optional, Union
from typing_extensions import TypeAlias

import ckan.plugins.toolkit as tk
from ckan.lib.redis import connect_to_redis, is_redis_available
from . import registry

CONFIG_ENABLED = "ckanext.ingest.enabled_types"
CONFIG_BASE_TEMPLATE = "ckanext.ingest.base_template"
DEFAULT_BASE_TEMPLATE = "page.html"
DEFAULT_ENABLED = []

TransformationSchema: TypeAlias = "dict[str, Rules]"


class StoreException(Exception):
    pass


@dataclasses.dataclass
class Options:
    alias: Optional[str] = None
    normalize_choice: bool = False
    choice_separator: str = ", "


class Rules(NamedTuple):
    options: Options
    field: dict[str, Any]


def store_record(record, fmt):
    if not is_redis_available():
        raise StoreException("Redis is not available")
    conn = connect_to_redis()
    key = "ckanext:ingest:queue:{}".format(fmt)
    conn.rpush(key, json.dumps(record))
    conn.expire(key, 3600 * 24)


def get_index_path():
    """Return path for registration ingest route."""
    return tk.config.get("ckanext.ingest.index_path", "/ckan-admin/ingest")


def get_base_template():
    """Return parent template for ingest page."""
    return tk.config.get(CONFIG_BASE_TEMPLATE, DEFAULT_BASE_TEMPLATE)


def get_ingestiers():
    """Return names of enabled ingestion formats."""
    allowed = set(tk.aslist(tk.config.get(CONFIG_ENABLED, DEFAULT_ENABLED)))
    items = list(registry)
    if allowed:
        items = [i for i in items if i[0] in allowed]
    return items


def get_ingestier(name):
    """Return implementation of specified ingester."""
    for n, instance in registry.registry:
        if name == n:
            return instance
    return None


def _get_transformation_schema(type_: str, fieldset: str) -> TransformationSchema:
    schema = tk.h.scheming_get_dataset_schema(type_)
    if not schema:
        raise TypeError(f"Schema {type_} does not exist")
    fields = f"{fieldset}_fields"

    return {
        f["field_name"]: Rules(Options(**(f["ingest_options"] or {})), f)
        for f in schema[fields]
        if "ingest_options" in f
    }


def _transform(data: dict[str, Any], schema: TransformationSchema) -> dict[str, Any]:
    result = {}
    for field, rules in schema.items():
        k = rules.options.alias or rules.field["label"]
        if k not in data:
            continue

        result[field] = data[k]

        if rules.options.normalize_choice:
            result[field] = _normalize_choice(
                result[field],
                tk.h.scheming_field_choices(rules.field),
                rules.options.choice_separator,
            )

    return result


def _normalize_choice(
    value: Union[str, list[str], None], choices: list[dict[str, str]], separator: str
) -> Union[str, list[str], None]:
    if not value:
        return

    if not isinstance(value, list):
        value = value.split(separator)

    mapping = {o["label"]: o["value"] for o in choices if "label" in o}
    value = [mapping.get(v, v) for v in value]

    if len(value) > 1:
        return value

    return value[0]


def transform_package(
    data_dict: dict[str, Any], type_: str = "dataset"
) -> dict[str, Any]:
    schema = _get_transformation_schema(type_, "dataset")
    return _transform(data_dict, schema)


def transform_resoruce(
    data_dict: dict[str, Any], type_: str = "dataset"
) -> dict[str, Any]:
    schema = _get_transformation_schema(type_, "resource")
    return _transform(data_dict, schema)
