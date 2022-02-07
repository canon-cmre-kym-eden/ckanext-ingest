from __future__ import annotations
import abc
import logging
from typing import IO, Any, Callable, Iterable, NamedTuple, Optional
from typing_extensions import TypedDict

log = logging.getLogger(__name__)


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
    @abc.abstractmethod
    def extract(
        self, source: IO[bytes], extras: Optional[ParsingExtras] = None
    ) -> Iterable[Any]:
        return []
