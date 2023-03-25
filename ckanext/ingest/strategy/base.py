from __future__ import annotations

import abc
import logging
import re
from typing import IO, Any, Callable, ClassVar, Iterable, Optional

from typing_extensions import TypedDict
from werkzeug.datastructures import FileStorage

from ..record import Record

log = logging.getLogger(__name__)
CASE_SWAP = re.compile("(?<=[a-z0-9])(?=[A-Z])")


class ParsingExtras(TypedDict, total=False):
    file_locator: Callable[[str], Optional[IO[bytes]]]


class Handler:
    data: Optional[Any]

    def __init__(self, strategy: ParsingStrategy):
        self.data = None
        self.strategy = strategy

    def parse(self, source: FileStorage, extras: Optional[ParsingExtras] = None):
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
    def can_handle(cls, mime: Optional[str], source: FileStorage) -> bool:
        return mime in cls.mimetypes

    @classmethod
    def must_handle(cls, mime: Optional[str], source: FileStorage) -> bool:
        return False

    @abc.abstractmethod
    def extract(
        self, source: FileStorage, extras: Optional[ParsingExtras] = None
    ) -> Iterable[Record]:
        return []
