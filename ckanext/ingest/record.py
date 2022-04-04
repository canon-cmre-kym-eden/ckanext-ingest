from __future__ import annotations
import abc

import dataclasses
from typing import Any

import ckan.model as model
import ckan.plugins.toolkit as tk

from . import transform


@dataclasses.dataclass
class Options:
    update_existing: bool = False
    verbose: bool = False


@dataclasses.dataclass
class Record(abc.ABC):
    raw: dict[str, Any]
    data: dict[str, Any] = dataclasses.field(init=False)
    options: Options = dataclasses.field(default_factory=Options, init=False)

    def __post_init__(self):
        self.data = self.transform(self.raw)

    def transform(self, raw):
        return raw

    def fill(self, defaults: dict[str, Any], overrides: dict[str, Any]):
        self.data = {**defaults, **self.data, **overrides}

    @abc.abstractmethod
    def ingest(self, context: dict[str, Any]):
        pass

    def set_options(self, data: dict[str, Any]):
        fields = {f.name for f in dataclasses.fields(self.options)}

        self.options = Options(**{k: v for k, v in data.items() if k in fields})


@dataclasses.dataclass
class TypedRecord(Record):
    type: str

    @classmethod
    def type_factory(cls, type_: str):
        return lambda *a, **k: cls(*a, type=type_, **k)


@dataclasses.dataclass
class PackageRecord(TypedRecord):
    type: str = "dataset"

    def transform(self, raw):
        data = transform.transform_package(raw, self.type)
        return data

    def ingest(self, context: dict[str, Any]):
        exists = (
            model.Package.get(self.data.get("id", self.data.get("name"))) is not None
        )
        action = "package_" + (
            "update" if exists and self.options.update_existing else "create"
        )
        result = tk.get_action(action)(context, self.data)
        if self.options.verbose:
            return result

        return {
            "id": result["id"],
            "type": result["type"],
            "action": action,
        }


@dataclasses.dataclass
class ResourceRecord(TypedRecord):
    type: str = "dataset"

    def transform(self, raw):
        data = transform.transform_resource(raw, self.type)
        return data

    def ingest(self, context: dict[str, Any]):
        existing = model.Resource.get(self.data.get("id", ""))
        exists = existing and existing.state == "active"
        action = "resource_" + (
            "update" if exists and self.options.update_existing else "create"
        )

        result = tk.get_action(action)(context, self.data)
        if self.options.verbose:
            return result
        return {
            "id": result["id"],
            "package_id": result["package_id"],
            "action": action,
        }
