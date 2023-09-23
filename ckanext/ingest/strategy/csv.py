from __future__ import annotations

import csv
import logging
from io import StringIO

from ckanext.ingest.record import PackageRecord
from ckanext.ingest.shared import ParsingStrategy, Storage, StrategyOptions

log = logging.getLogger(__name__)


class CsvStrategy(ParsingStrategy):
    """Transform CSV rows into datasets using ckanext-scheming.

    Every scheming field that has `ingest_options` attribute defines how data
    from the row maps into metadata schema. For example, if `notes` field has
    `ingest_options: {aliases: [DESCRIPTION]}`, `DESCRIPTION` column from CSV
    will be used as a data source for this field.

    """

    mimetypes = {"text/csv"}
    record_factory = PackageRecord

    def chunks(self, source: Storage, options: StrategyOptions):
        return csv.DictReader(StringIO(source.read().decode()))
