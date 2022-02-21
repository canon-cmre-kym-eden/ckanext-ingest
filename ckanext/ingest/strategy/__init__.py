from __future__ import annotations

from typing import IO, Optional, Type
from .base import Handler, ParsingStrategy
from .. import registry

__all__ = ["Handler", "get_handler", "ParsingStrategy"]

strategies = registry.Registry[Type[ParsingStrategy]]()


def get_handler(mime: Optional[str], source: IO[bytes]) -> Optional[Handler]:
    for strategy in strategies:
        if strategy.can_handle(mime, source):
            return Handler(strategy())
