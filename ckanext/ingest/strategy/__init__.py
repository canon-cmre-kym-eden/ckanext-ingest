from __future__ import annotations

from typing import Any, Optional, Type
from .base import Handler, PackageRecord, ResourceRecord, ParsingStrategy
from .. import registry

__all__ = ["PackageRecord", "ResourceRecord", "Handler", "get_handler", "ParsingStrategy"]

strategies = registry.Registry[Type[ParsingStrategy]]()

def get_handler(mime: Any) -> Optional[Handler]:
    for strategy in strategies:
        if strategy.can_handle(mime):
            return Handler(strategy())
