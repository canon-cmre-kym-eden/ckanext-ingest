# -*- coding: utf-8 -*-
import json

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.redis import connect_to_redis, is_redis_available

from ckanext.ingest.interfaces import IIngest

_ingesters = []


class StoreException(Exception):
    pass


class IngestPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, '../templates')
        toolkit.add_public_directory(config_, '../public')
        toolkit.add_resource('fanstatic', '../ingest')

        use_pylons = get_pylons_preference()
        self._load_platform_plugin(use_pylons)

    # IConfigurable

    def configure(self, config_):
        _ingesters[:] = []
        for plugin in plugins.PluginImplementations(IIngest):
            _ingesters.extend(plugin.get_ingesters())

    @staticmethod
    def _load_platform_plugin(use_pylons=False):
        if not use_pylons and toolkit.check_ckan_version('2.8'):
            if not plugins.plugin_loaded('ingest_flask'):
                plugins.load('ingest_flask')
        else:
            if not plugins.plugin_loaded('ingest_pylons'):
                plugins.load('ingest_pylons')


def store_record(record, fmt):
    if not is_redis_available():
        raise StoreException('Redis is not available')
    conn = connect_to_redis()
    key = 'ckanext:ingest:queue:{}'.format(fmt)
    conn.rpush(key, json.dumps(record))
    conn.expire(key, 3600 * 24)


def get_index_path():
    """Return path for registration ingest route.
    """
    return toolkit.config.get(
        u'ckanext.ingest.index_path', u'/ckan-admin/ingest'
    )


def get_pylons_preference():
    """Check whether pylons-plugin must be used disregarding current CKAN
    version.
    """
    return toolkit.asbool(toolkit.config.get('ckanext.ingest.force_pylons'))


def get_access_check():
    """Access function to call in order to authorize access ti ingestion pages.
    """
    return toolkit.config.get('ckanext.ingest.access_check', 'sysadmin')


def get_base_template():
    """Return parent template for ingest page.
    """
    return toolkit.config.get(
        'ckanext.ingest.base_template', 'admin/base.html'
    )


def get_main_template():
    """Return main template for ingest page.
    """
    return toolkit.config.get(
        'ckanext.ingest.main_template', 'ingest/index.html'
    )


def get_ingestiers():
    """Return names of enabled ingestion formats.
    """
    allowed = set(
        toolkit.aslist(
            toolkit.config.get('ckanext.ingest.ingestion_formats', [])
        )
    )
    items = _ingesters
    if allowed:
        items = [i for i in items if i[0] in allowed]
    return items


def get_ingestier(name):
    """Return implementation of specified ingester.
    """
    for n, instance in _ingesters:
        if name == n:
            return instance
    return None
