from __future__ import annotations


from werkzeug.datastructures import FileStorage

from ckanext.ingest import registry
from .base import Handler, ParsingStrategy

__all__ = ["Handler", "get_handler", "ParsingStrategy"]

strategies: registry.Registry[type[ParsingStrategy]] = registry.Registry()


def get_handler(mime: str | None, source: FileStorage) -> Handler | None:
    choices = []
    for strategy in strategies:
        if not strategy.can_handle(mime, source):
            continue

        if strategy.must_handle(mime, source):
            return Handler(strategy())

        choices.append(strategy)

    if choices:
        return Handler(choices[0]())
    return None
