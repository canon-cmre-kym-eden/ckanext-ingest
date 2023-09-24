from __future__ import annotations

import dataclasses
from typing import Any

import ckan.plugins.toolkit as tk
from ckan import model, types

from . import config, shared, transform


@dataclasses.dataclass
class PackageRecord(shared.Record):
    """Package mapped from raw data via metadata schema.

    Options:

        extras["profile"]: transformation profile. Defines the name of scheming
        field's attribute `{profile}_options` that contains transformation
        rules.

    """

    type: str = "dataset"
    profile: str = dataclasses.field(init=False)

    def __post_init__(self):
        self.profile = self.options.get("extras", {}).get("profile", "ingest")
        super().__post_init__()

    def transform(self, raw: Any):
        return transform.transform_package(raw, self.type, self.profile)

    def ingest(self, context: types.Context) -> shared.IngestionResult:
        id_or_name = self.data.get("id", self.data.get("name"))
        pkg = model.Package.get(id_or_name)

        action = "package_" + (
            "update" if pkg and self.options.get("update_existing") else "create"
        )
        result = tk.get_action(action)(context, self.data)

        return {
            "success": True,
            "result": result,
            "details": {"action": action},
        }


@dataclasses.dataclass
class ResourceRecord(shared.Record):
    """Package mapped from raw data via metadata schema.

    Options:

        extras["profile"]: transformation profile. Defines the name of scheming
        field's attribute `{profile}_options` that contains transformation
        rules.

    """

    type: str = "dataset"
    profile: str = dataclasses.field(init=False)

    def __post_init__(self):
        self.profile = self.options.get("extras", {}).get("profile", "ingest")

        super().__post_init__()

    def transform(self, raw: Any):
        return transform.transform_resource(raw, self.type, self.profile)

    def ingest(self, context: types.Context) -> shared.IngestionResult:
        existing = model.Resource.get(self.data.get("id", ""))
        prefer_update = existing and existing.state == "active"

        if (
            existing
            and prefer_update
            and existing.package_id != self.data.get("package_id")
        ):
            if config.allow_transfer():
                prefer_update = False

            else:
                raise tk.ValidationError(
                    {
                        "id": (
                            "Resource already belogns to the package"
                            f" {existing.package_id} and cannot be transfered"
                            f" to {self.data.get('package_id')}"
                        ),
                    },
                )

        action = "resource_" + (
            "update"
            if prefer_update and self.options.get("update_existing")
            else "create"
        )

        result = tk.get_action(action)(context, self.data)
        return {
            "success": True,
            "result": result,
            "details": {"action": action},
        }
