# -*- coding: utf-8 -*-

from ckan.plugins.interfaces import Interface


class IIngest(Interface):
    """Hook into ckanext-ingest.
    """

    def get_ingesters(self):
        """Return list of (name, instance) pairs for Ingester implementations.

        """
        return []
