from __future__ import annotations

from typing import Type

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

from . import cli, interfaces, strategy, views
from .logic import action, auth, validators

CONFIG_WHITELIST = "ckanext.ingest.strategy.whitelist"
DEFAULT_WHITELIST = []


class IngestPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(interfaces.IIngest, inherit=True)

    # IValidators
    def get_validators(self):
        return validators.get_validators()

    # IBlueprint
    def get_blueprint(self):
        return views.get_blueprints()

    # IClick
    def get_commands(self):
        return cli.get_commnads()

    # IConfigurer

    def update_config(self, config_):
        tk.add_template_directory(config_, "templates")

    # IConfigurable

    def configure(self, config_):
        strategy.strategies.reset()
        whitelist = tk.aslist(tk.config.get(CONFIG_WHITELIST, DEFAULT_WHITELIST))
        for plugin in plugins.PluginImplementations(interfaces.IIngest):
            items = plugin.get_ingest_strategies()
            if whitelist:
                items = [item for item in items if item.name() in whitelist]
            strategy.strategies.extend(items)

    # IActions
    def get_actions(self):
        return action.get_actions()

    # IAuthFunctions
    def get_auth_functions(self):
        return auth.get_auth_functions()

    # IIngest
    def get_ingest_strategies(self) -> list[Type[strategy.ParsingStrategy]]:
        from .strategy import csv, xlsx, zip

        return [
            zip.ZipStrategy,
            xlsx.SeedExcelStrategy,
            csv.CsvStrategy,
        ]
