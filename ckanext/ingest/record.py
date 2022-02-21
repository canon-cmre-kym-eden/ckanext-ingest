from __future__ import annotations

import dataclasses
from typing import Any
from . import transform


@dataclasses.dataclass
class Record:
    raw: dataclasses.InitVar[dict[str, Any]]
    data: dict[str, Any] = dataclasses.field(init=False)

    def __post_init__(self, raw):
        self.data = self.transform(raw)

    def transform(self, raw):
        return raw


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


@dataclasses.dataclass
class ResourceRecord(TypedRecord):
    type: str = "dataset"

    def transform(self, raw):
        data = transform.transform_resource(raw, self.type)
        return data
