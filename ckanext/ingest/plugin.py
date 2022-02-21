from __future__ import annotations
from typing import Type

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

from . import interfaces, views, cli, strategy
from .logic import action, auth


class IngestPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(interfaces.IIngest, inherit=True)

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

        for plugin in plugins.PluginImplementations(interfaces.IIngest):
            strategy.strategies.extend(plugin.get_ingest_strategies())

    # IActions
    def get_actions(self):
        return action.get_actions()

    # IAuthFunctions
    def get_auth_functions(self):
        return auth.get_auth_functions()

    # IIngest
    def get_ingest_strategies(self) -> list[Type[strategy.ParsingStrategy]]:
        from .strategy import zip, xlsx, csv

        return [
            zip.ZipStrategy,
            xlsx.SeedExcelStrategy,
            csv.CsvStrategy,
        ]
