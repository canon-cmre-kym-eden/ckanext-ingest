from __future__ import annotations


import dataclasses
from typing import Any

from ckan import model, types
import ckan.plugins.toolkit as tk

from . import transform, config, shared


@dataclasses.dataclass
class PackageRecord(shared.Record):
    type: str = "dataset"
    profile: str = "ingest"

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
    type: str = "dataset"
    profile: str = "ingest"

    def transform(self, raw: Any):
        return transform.transform_resource(raw, self.type, self.profile)

    def ingest(self, context: types.Context) -> shared.IngestionResult:
        existing = model.Resource.get(self.data.get("id", ""))
        prefer_update = existing and existing.state == "active"


        if existing and prefer_update and existing.package_id != self.data.get("package_id"):
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
            "update" if prefer_update and self.options.get("update_existing") else "create"
        )

        result = tk.get_action(action)(context, self.data)
        return {
            "success": True,
            "result": result,
            "details": {"action": action},
        }
