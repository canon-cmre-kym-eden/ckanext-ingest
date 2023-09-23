from __future__ import annotations

import csv
import logging
from io import StringIO

from werkzeug.datastructures import FileStorage

from ckanext.ingest.record import PackageRecord
from ckanext.ingest.shared import StrategyOptions, ParsingStrategy

log = logging.getLogger(__name__)


class CsvStrategy(ParsingStrategy):
    mimetypes = {"text/csv"}
    record_factory = PackageRecord

    def chunks(self, source: FileStorage, options: StrategyOptions):
        return csv.DictReader(StringIO(source.read().decode()))
