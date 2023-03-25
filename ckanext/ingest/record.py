from __future__ import annotations

import abc
import dataclasses
from typing import Any

import ckan.model as model
import ckan.plugins.toolkit as tk

from . import transform

CONFIG_ALLOW_TRANSFER = "ckanext.ingest.allow_resource_transfer"
DEFAULT_ALLOW_TRANSFER = False


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
    def type_factory(cls, type_: str, **partial: Any):
        return lambda *a, **k: cls(*a, type=type_, **{**k, **partial})


@dataclasses.dataclass
class PackageRecord(TypedRecord):
    type: str = "dataset"
    profile: str = "ingest"

    def transform(self, raw):
        data = transform.transform_package(raw, self.type, self.profile)
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
    profile: str = "ingest"

    def transform(self, raw):
        data = transform.transform_resource(raw, self.type, self.profile)
        return data

    def ingest(self, context: dict[str, Any]):
        existing = model.Resource.get(self.data.get("id", ""))
        exists = existing and existing.state == "active"

        allow_transfer = tk.asbool(
            tk.config.get(CONFIG_ALLOW_TRANSFER, DEFAULT_ALLOW_TRANSFER)
        )
        if exists and existing.package_id != self.data.get("package_id"):
            if allow_transfer:
                exists = False
            else:
                raise tk.ValidationError(
                    {
                        "id": (
                            "Resource already belogns to the package"
                            f" {existing.package_id}"
                        )
                    }
                )

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
