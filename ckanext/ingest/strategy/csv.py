from __future__ import annotations

import csv
import logging
from io import StringIO
from typing import IO, Iterable, Optional, Type

from werkzeug.datastructures import FileStorage

from ..record import PackageRecord, Record
from .base import ParsingExtras, ParsingStrategy

log = logging.getLogger(__name__)


class CsvStrategy(ParsingStrategy):
    mimetypes = {"text/csv"}

    def extract(
        self, source: FileStorage, extras: Optional[ParsingExtras] = None
    ) -> Iterable[Record]:
        reader = csv.DictReader(StringIO(source.read().decode()))
        yield from map(self._record_factory(source, extras), reader)

    def _record_factory(
        self, source: FileStorage, extras: Optional[ParsingExtras] = None
    ) -> Type[Record]:
        return PackageRecord
