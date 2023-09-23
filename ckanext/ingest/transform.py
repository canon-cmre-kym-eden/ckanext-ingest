from __future__ import annotations

import dataclasses
from typing import Any

from typing_extensions import TypeAlias

import ckan.plugins.toolkit as tk

TransformationSchema: TypeAlias = "dict[str, Rules]"


@dataclasses.dataclass
class Options:
    """Transformation options taken from `{profile}_options` attribute of field
    in ckanext-scheming's schema

    These options define how raw value passed into the Record transforms into
    proper value that is suitable for the entity's schema. Workflow is the
    following:

    * parse the source
    * get raw data dict
    * transform every field defined in metadata schema and available in raw
      data using Options into
    * pass transformed data to CKAN API action

    """
    # names of the field in the raw data
    aliases: list[str] = dataclasses.field(default_factory=list)

    # transform select label[s] into value[s]
    normalize_choice: bool = False

    # used by `normalize_choice`. Split raw value into multiple values using
    # given separator
    choice_separator: str = ", "

    # convert raw field using validators. Validation errors are ignored.
    convert: str = ""

    def __post_init__(self):
        if isinstance(self.aliases, str):
            self.aliases = [self.aliases]


@dataclasses.dataclass
class Rules:
    options: Options
    field: dict[str, Any]
    schema: dict[str, Any]


def transform_package(
    data_dict: dict[str, Any],
    type_: str = "dataset",
    profile: str = "ingest",
) -> dict[str, Any]:
    schema = _get_transformation_schema(type_, "dataset", profile)
    result = _transform(data_dict, schema)
    result.setdefault("type", type_)
    return result


def transform_resource(
    data_dict: dict[str, Any],
    type_: str = "dataset",
    profile: str = "ingest",
) -> dict[str, Any]:
    schema = _get_transformation_schema(type_, "resource", profile)
    return _transform(data_dict, schema)


def _get_transformation_schema(
    type_: str,
    fieldset: str,
    profile: str,
) -> TransformationSchema:
    schema = tk.h.scheming_get_dataset_schema(type_)
    if not schema:
        raise ValueError(type_)
    fields = f"{fieldset}_fields"

    return {
        f["field_name"]: Rules(Options(**(f[f"{profile}_options"] or {})), f, schema)
        for f in schema[fields]
        if "ingest_options" in f
    }


def _transform(data: dict[str, Any], schema: TransformationSchema) -> dict[str, Any]:
    from ckanext.scheming.validation import validators_from_string
    validators_from_string: Any

    result: dict[str, Any] = {}

    for field, rules in schema.items():
        for k in rules.options.aliases or [rules.field["field_name"], rules.field["label"]]:
            if k in data:
                break
        else:
            continue

        validators = validators_from_string(
            rules.options.convert,
            rules.field,
            rules.schema,
        )
        valid_data, _err = tk.navl_validate(data, {k: validators})

        if k not in valid_data:
            continue

        value = valid_data[k]
        if rules.options.normalize_choice:
            value = _normalize_choice(
                value,
                tk.h.scheming_field_choices(rules.field),
                rules.options.choice_separator,
            )
        result[field] = value

    return result


def _normalize_choice(
    value: str | list[str] | None,
    choices: list[dict[str, str]],
    separator: str,
) -> str | list[str] | None:
    if not value:
        return None

    if not isinstance(value, list):
        value = value.split(separator)

    mapping = {o["label"]: o["value"] for o in choices if "label" in o}
    value = [mapping.get(v, v) for v in value]

    if len(value) > 1:
        return value

    return value[0]
