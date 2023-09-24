from __future__ import annotations

from ckan.plugins.interfaces import Interface

from . import shared


class IIngest(Interface):
    """Hook into ckanext-ingest."""

    def get_ingest_strategies(
        self,
    ) -> dict[str, type[shared.ExtractionStrategy]]:
        """Return parsing strategies."""
        return {}
