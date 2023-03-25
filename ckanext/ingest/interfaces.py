from __future__ import annotations

from typing import Iterable, Type

from ckan.plugins.interfaces import Interface

from . import strategy


class IIngest(Interface):
    """Hook into ckanext-ingest."""

    def get_ingest_strategies(
        self,
    ) -> Iterable[Type[strategy.ParsingStrategy]]:
        """Return an iterable of provided parsing strategies."""
        return []
