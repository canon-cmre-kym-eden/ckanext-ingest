from __future__ import annotations

import abc
import logging
import re
from typing import IO, Any, Callable, ClassVar, Iterable

from typing_extensions import TypedDict
from werkzeug.datastructures import FileStorage

from ckanext.ingest.record import Record

log = logging.getLogger(__name__)
CASE_SWAP = re.compile("(?<=[a-z0-9])(?=[A-Z])")


class ParsingExtras(TypedDict, total=False):
    file_locator: Callable[[str], IO[bytes] | None]


class Handler:
    data: Any | None

    def __init__(self, strategy: ParsingStrategy):
        self.data = None
        self.strategy = strategy

    def parse(self, source: FileStorage, extras: ParsingExtras | None = None):
        return self.strategy.extract(source, extras)


class ParsingStrategy(abc.ABC):
    mimetypes: ClassVar[set[str]] = set()

    @classmethod
    def name(cls) -> str:
        parts = CASE_SWAP.split(cls.__name__)
        if parts[-1] == "Strategy":
            parts.pop()
        return "_".join(map(str.lower, parts))

    @classmethod
    def can_handle(cls, mime: str | None, source: FileStorage) -> bool:
        return mime in cls.mimetypes

    @classmethod
    def must_handle(cls, mime: str | None, source: FileStorage) -> bool:
        return False

    @abc.abstractmethod
    def extract(
        self, source: FileStorage, extras: ParsingExtras | None = None,
    ) -> Iterable[Record]:
        return []
