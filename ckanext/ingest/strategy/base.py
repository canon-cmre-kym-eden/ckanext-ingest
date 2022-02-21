from __future__ import annotations
import re
import abc
import logging
from typing import IO, Any, Callable, ClassVar, Iterable, NamedTuple, Optional
from typing_extensions import TypedDict

log = logging.getLogger(__name__)
CASE_SWAP = re.compile("(?<=[a-z0-9])(?=[A-Z])")

class PackageRecord(NamedTuple):
    data: dict[str, Any]


class ResourceRecord(NamedTuple):
    data: dict[str, Any]


class ParsingExtras(TypedDict, total=False):
    file_locator: Callable[[str], Optional[IO[bytes]]]


class Handler:
    data: Optional[Any]

    def __init__(self, strategy: ParsingStrategy):
        self.data = None
        self.strategy = strategy

    def parse(self, source: IO[bytes], extras: Optional[ParsingExtras] = None):

        self.records = self.strategy.extract(source, extras)


class ParsingStrategy(abc.ABC):
    mimetypes: ClassVar[set[str]] = set()

    @classmethod
    def name(cls) -> str:
        parts = CASE_SWAP.split(cls.__name__)
        if parts[-1] == "Strategy":
            parts.pop()
        return "_".join(map(str.lower, parts))


    @classmethod
    def can_handle(cls, mime: str) -> bool:
        return mime in cls.mimetypes

    @abc.abstractmethod
    def extract(
        self, source: IO[bytes], extras: Optional[ParsingExtras] = None
    ) -> Iterable[Any]:
        return []
