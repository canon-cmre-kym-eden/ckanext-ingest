from __future__ import annotations

import csv
import logging
from io import StringIO
from typing import Iterable

from werkzeug.datastructures import FileStorage

from ckanext.ingest.record import PackageRecord
from ckanext.ingest.shared import StrategyOptions, ParsingStrategy, Record

log = logging.getLogger(__name__)


class CsvStrategy(ParsingStrategy):
    mimetypes = {"text/csv"}

    def extract(
        self, source: FileStorage, options: StrategyOptions | None = None,
    ) -> Iterable[Record]:
        reader = csv.DictReader(StringIO(source.read().decode()))
        yield from map(self._record_factory(source, options), reader)

    def _record_factory(
        self, source: FileStorage, extras: StrategyOptions | None = None,
    ) -> type[Record]:
        return PackageRecord
