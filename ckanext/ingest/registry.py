from __future__ import annotations

from typing import Generic, Iterable, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    items: list[T]

    def __init__(self):
        self.items = []

    def reset(self):
        self.items[:] = []

    def extend(self, ingestors: Iterable[T]):
        self.items.extend(ingestors)

    def __iter__(self):
        return iter(self.items)
