from __future__ import annotations

from ckan import common

from ckan import plugins
import ckan.plugins.toolkit as tk

from . import interfaces, strategy

CONFIG_WHITELIST = "ckanext.ingest.strategy.whitelist"
DEFAULT_WHITELIST = []


@tk.blanket.auth_functions
@tk.blanket.actions
@tk.blanket.validators
@tk.blanket.cli
@tk.blanket.blueprints
class IngestPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(interfaces.IIngest, inherit=True)

    # IConfigurer

    def update_config(self, config_: common.CKANConfig):
        tk.add_template_directory(config_, "templates")

    # IConfigurable

    def configure(self, config_: common.CKANConfig):
        strategy.strategies.reset()
        whitelist = tk.aslist(tk.config.get(CONFIG_WHITELIST, DEFAULT_WHITELIST))
        for plugin in plugins.PluginImplementations(interfaces.IIngest):
            items = plugin.get_ingest_strategies()
            if whitelist:
                items = [item for item in items if item.name() in whitelist]
            strategy.strategies.extend(items)

    # IIngest
    def get_ingest_strategies(self) -> list[type[strategy.ParsingStrategy]]:
        from .strategy import csv, xlsx, zip

        return [
            zip.ZipStrategy,
            xlsx.SeedExcelStrategy,
            csv.CsvStrategy,
        ]
