from __future__ import annotations
from ckan import types

import abc
import logging
import dataclasses
from typing import Any, ClassVar, Iterable

from typing_extensions import TypedDict
from werkzeug.datastructures import FileStorage

from werkzeug.datastructures import FileStorage

log = logging.getLogger(__name__)

strategies: dict[str, type[ParsingStrategy]] = {}

class RecordOptions(TypedDict, total=False):
    """Options for Record extracted by Strategy.
    """
    # trigger an update if the data produced by the record already exists
    update_existing: bool

    # return more details after producing the data
    verbose: bool


class StrategyOptions(TypedDict, total=False):
    """Options for Strategy.
    """
    # options passed into every record produced by the strategy
    record_options: dict[str, Any]


class IngestionResult(TypedDict, total=False):
    """Outcome of the record ingestion.
    """
    # created/updated data
    result: Any
    # indicator of successful ingestion
    success: bool
    # additional details about ingestion
    details: dict[str, Any]


@dataclasses.dataclass
class Record(abc.ABC):
    """Single element produced by extraction strategy.

    The record is responsible for creating/updating the data.
    """

    # original data extracted by strategy
    raw: dict[str, Any]

    # transformed data adapted to the record needs
    data: dict[str, Any] = dataclasses.field(init=False)

    # options received from extraction strategy
    options: RecordOptions = dataclasses.field(default_factory=RecordOptions)

    def __post_init__(self):
        self.data = self.transform(self.raw)

    def transform(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Transform arbitrary data into a data that has sense for a record.
        """
        return raw

    def fill(self, defaults: dict[str, Any], overrides: dict[str, Any]):
        """Apply default and overrides to the data.
        """
        self.data = {**defaults, **self.data, **overrides}

    @abc.abstractmethod
    def ingest(self, context: types.Context) -> IngestionResult:
        """Create/update something using the data.
        """
        pass



class ParsingStrategy(abc.ABC):
    """Record extraction strategy.

    This class is repsonsible for parsing the source and yielding record
    instances from it.

    Attributes:
        mimetypes: collection of mimetypes supported by the strategy
    """

    mimetypes: ClassVar[set[str]] = set()

    @classmethod
    def can_handle(cls, mime: str | None, source: FileStorage) -> bool:
        """Check if strategy can handle given mimetype/source.
        """
        return mime in cls.mimetypes

    @classmethod
    def must_handle(cls, mime: str | None, source: FileStorage) -> bool:
        """Check if strategy is the best choice for handling given mimetype/source.
        """
        return False

    @abc.abstractmethod
    def extract(
        self,
        source: FileStorage,
        options: StrategyOptions,
    ) -> Iterable[Record]:
        """Return iterable over all records extracted from source.

        `extras` contains settings, helpers and other artifacts that can help
        during extraction. It's passed by user or generated/modified by other
        strategies, so there are no guarantees or rules when you are using it.

        """
        return []


def get_handler_for_mimetype(mime: str | None, source: FileStorage) -> ParsingStrategy | None:
    """Select the most suitable handler for the MIMEType.

    The first strategy that `must_handle` is returned. If there is no such
    strategy, the first that `can_handle` is returned.

    """
    choices: list[type[ParsingStrategy]] = []
    for strategy in strategies.values():
        if not strategy.can_handle(mime, source):
            continue

        if strategy.must_handle(mime, source):
            return strategy()

        choices.append(strategy)

    if choices:
        return choices[0]()

    return None
