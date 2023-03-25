from __future__ import annotations

import dataclasses
from typing import Any, NamedTuple, Optional, Union

from typing_extensions import TypeAlias

import ckan.plugins.toolkit as tk

from ckanext.scheming.validation import validators_from_string

TransformationSchema: TypeAlias = "dict[str, Rules]"


@dataclasses.dataclass
class Options:
    alias: list[str] = dataclasses.field(default_factory=list)
    normalize_choice: bool = False
    choice_separator: str = ", "
    convert: str = ""

    def __post_init__(self):
        if isinstance(self.alias, str):
            self.alias = [self.alias]


class Rules(NamedTuple):
    options: Options
    field: dict[str, Any]
    schema: dict[str, Any]


def transform_package(
    data_dict: dict[str, Any], type_: str = "dataset", profile: str = "ingest"
) -> dict[str, Any]:
    schema = _get_transformation_schema(type_, "dataset", profile)
    result = _transform(data_dict, schema)
    result.setdefault("type", type_)
    return result


def transform_resource(
    data_dict: dict[str, Any], type_: str = "dataset", profile: str = "ingest"
) -> dict[str, Any]:
    schema = _get_transformation_schema(type_, "resource", profile)
    return _transform(data_dict, schema)


def _get_transformation_schema(
    type_: str, fieldset: str, profile: str
) -> TransformationSchema:
    schema = tk.h.scheming_get_dataset_schema(type_)
    if not schema:
        raise TypeError(f"Schema {type_} does not exist")
    fields = f"{fieldset}_fields"

    return {
        f["field_name"]: Rules(Options(**(f[f"{profile}_options"] or {})), f, schema)
        for f in schema[fields]
        if "ingest_options" in f
    }


def _transform(data: dict[str, Any], schema: TransformationSchema) -> dict[str, Any]:
    result = {}

    for field, rules in schema.items():
        for k in rules.options.alias or [rules.field["label"]]:
            if k in data:
                break
        else:
            continue

        validators = validators_from_string(
            rules.options.convert, rules.field, rules.schema
        )
        valid_data, _err = tk.navl_validate(data, {k: validators})

        value = valid_data[k]
        if value == "":
            continue

        if rules.options.normalize_choice:
            value = _normalize_choice(
                value,
                tk.h.scheming_field_choices(rules.field),
                rules.options.choice_separator,
            )
        result[field] = value

    return result


def _normalize_choice(
    value: Union[str, list[str], None],
    choices: list[dict[str, str]],
    separator: str,
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
