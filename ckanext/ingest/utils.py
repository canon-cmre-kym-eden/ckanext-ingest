from __future__ import annotations
import json
from typing import Any
import ckan.plugins.toolkit as tk
from ckan.lib.redis import connect_to_redis, is_redis_available


class StoreException(Exception):
    pass


def store_record(record, fmt):
    if not is_redis_available():
        raise StoreException("Redis is not available")
    conn = connect_to_redis()
    key = "ckanext:ingest:queue:{}".format(fmt)
    conn.rpush(key, json.dumps(record))
    conn.expire(key, 3600 * 24)


def get_index_path():
    """Return path for registration ingest route."""
    return tk.config.get(u"ckanext.ingest.index_path", u"/ckan-admin/ingest")


def get_pylons_preference():
    """Check whether pylons-plugin must be used disregarding current CKAN
    version.
    """
    return tk.asbool(tk.config.get("ckanext.ingest.force_pylons"))


def get_access_check():
    """Access function to call in order to authorize access ti ingestion pages."""
    return tk.config.get("ckanext.ingest.access_check", "sysadmin")


def get_base_template():
    """Return parent template for ingest page."""
    return tk.config.get("ckanext.ingest.base_template", "admin/base.html")


def get_main_template():
    """Return main template for ingest page."""
    return tk.config.get("ckanext.ingest.main_template", "ingest/index.html")


def get_ingestiers():
    """Return names of enabled ingestion formats."""
    allowed = set(tk.aslist(tk.config.get("ckanext.ingest.ingestion_formats", [])))
    items = list(registry)
    if allowed:
        items = [i for i in items if i[0] in allowed]
    return items


def get_ingestier(name):
    """Return implementation of specified ingester."""
    for n, instance in registry:
        if name == n:
            return instance
    return None


class Registry:
    items: list[Any]

    def __init__(self):
        self.items = []

    def reset(self):
        self.items[:] = []

    def extend(self, ingestors):
        self.items.extend(ingestors)

    def __iter__(self):
        return iter(self.items)


registry = Registry()
