from __future__ import annotations

import logging
import mimetypes
import os
import zipfile
from io import BytesIO
from typing import Iterable

from ckanext.ingest import shared

log = logging.getLogger(__name__)


class ZipStrategy(shared.ParsingStrategy):
    """Recursively open ZIP archive and ingest every file inside it.

    Most suitable strategy is chosen for every file inside the archive. If no
    strategies found, file is ignored. Every nested ZIP archive ingested in the
    same manner as a top-level archive.

    """

    mimetypes = {"application/zip"}

    def _make_locator(self, archive: zipfile.ZipFile):
        def locator(name: str):
            try:
                return archive.open(name)
            except KeyError:
                log.warning(
                    "File %s not found in the archive %s",
                    name,
                    archive.filename,
                )

        return locator

    def extract(
        self,
        source: shared.Storage,
        options: shared.StrategyOptions,
    ) -> Iterable[shared.Record]:
        with zipfile.ZipFile(BytesIO(source.read())) as archive:
            for item in archive.namelist():
                mime, _encoding = mimetypes.guess_type(item)
                handler = shared.get_handler_for_mimetype(
                    mime,
                    shared.make_file_storage(
                        archive.open(item), os.path.basename(item), mime,
                    ),
                )
                if not handler:
                    log.debug("Skip %s with MIMEType %s", item, mime)
                    continue

                yield from handler.extract(
                    shared.make_file_storage(archive.open(item)),
                    {"file_locator": self._make_locator(archive)},
                )
