from __future__ import annotations
from typing import Iterable

from . import strategy


class Registry:
    items: list[strategy.ParsingStrategy]

    def __init__(self):
        self.items = []

    def reset(self):
        self.items[:] = []

    def extend(self, ingestors: Iterable[strategy.ParsingStrategy]):
        self.items.extend(ingestors)

    def __iter__(self):
        return iter(self.items)


registry = Registry()
