from __future__ import annotations

import ckan.plugins.toolkit as tk
from ckan import common, plugins

from . import config, interfaces, shared


@tk.blanket.auth_functions
@tk.blanket.actions
@tk.blanket.validators
@tk.blanket.cli
@tk.blanket.blueprints
@tk.blanket.config_declarations
class IngestPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(interfaces.IIngest, inherit=True)

    # IConfigurer

    def update_config(self, config_: common.CKANConfig):
        tk.add_template_directory(config_, "templates")

    # IConfigurable

    def configure(self, config_: common.CKANConfig):
        shared.strategies.clear()

        whitelist = config.allowed_strategies()
        blacklist = config.disabled_strategies()
        name_mapping = config.name_mapping()

        for plugin in plugins.PluginImplementations(interfaces.IIngest):
            for name, s in plugin.get_ingest_strategies().items():
                final_name = name_mapping.get(f"{s.__module__}:{s.__name__}", name)

                if whitelist and final_name not in whitelist:
                    continue

                if final_name in blacklist:
                    continue

                shared.strategies.update({final_name: s})

    # IIngest
    def get_ingest_strategies(self) -> dict[str, type[shared.ExtractionStrategy]]:
        from .strategy import csv, xlsx, zip

        strategies = {
            "ingest:recursive_zip": zip.ZipStrategy,
            "ingest:scheming_csv": csv.CsvStrategy,
        }
        if xlsx.is_installed:
            strategies["ingest:xlsx"] = xlsx.XlsxStrategy

        return strategies
