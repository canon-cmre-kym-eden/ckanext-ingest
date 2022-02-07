from __future__ import annotations

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

from . import interfaces, views, cli, registry
from .logic import action, auth


class IngestPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)

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
        registry.registry.reset()

        for plugin in plugins.PluginImplementations(interfaces.IIngest):
            registry.registry.extend(plugin.get_ingest_strategies())

    # IActions
    def get_actions(self):
        return action.get_actions()

    # IAuthFunctions
    def get_auth_functions(self):
        return auth.get_auth_functions()
