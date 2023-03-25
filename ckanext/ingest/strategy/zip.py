from __future__ import annotations

import logging
import mimetypes
import zipfile
from io import BytesIO
from typing import IO, Any, Iterable, Optional

from werkzeug.datastructures import FileStorage

from .base import ParsingExtras, ParsingStrategy

log = logging.getLogger(__name__)


class ZipStrategy(ParsingStrategy):
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
        self, source: FileStorage, extras: Optional[ParsingExtras] = None
    ) -> Iterable[Any]:
        from . import get_handler

        with zipfile.ZipFile(BytesIO(source.read())) as archive:
            for item in archive.namelist():
                mime, _encoding = mimetypes.guess_type(item)
                handler = get_handler(mime, FileStorage(archive.open(item)))
                if not handler:
                    log.debug("Skip %s with MIMEType %s", item, mime)
                    continue

                yield from handler.parse(
                    FileStorage(archive.open(item)),
                    {"file_locator": self._make_locator(archive)},
                )
