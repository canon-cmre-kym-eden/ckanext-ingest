from __future__ import annotations

import logging
import mimetypes
import os
import zipfile
from fnmatch import fnmatch
from io import BytesIO
from typing import IO, Callable, Iterable

from typing_extensions import TypedDict

from ckanext.ingest import shared

log = logging.getLogger(__name__)


class ZipChunk(TypedDict):
    handler: shared.ExtractionStrategy
    name: str
    source: shared.Storage
    file_locator: Callable[[str], IO[bytes]]


class ZipStrategy(shared.ExtractionStrategy):
    """Recursively open ZIP archive and ingest every file inside it.

    Most suitable strategy is chosen for every file inside the archive. If no
    strategies found, file is ignored. Every nested ZIP archive ingested in the
    same manner as a top-level archive.

    Options:

        nested_strategy: extraction strategy applied to files in the archive. By
        default, strategy is defined based on file's mimetype

        extras["glob"]: ingest only files matching the pattern
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

    def chunks(
        self,
        source: shared.Storage,
        options: shared.StrategyOptions,
    ) -> Iterable[ZipChunk]:
        with zipfile.ZipFile(BytesIO(source.read())) as archive:
            file_locator = self._make_locator(archive)
            glob: str = options.get("extras", {}).get("glob", "")

            for item in archive.namelist():
                if glob and not fnmatch(item, glob):
                    continue

                mime, _encoding = mimetypes.guess_type(item)
                if strategy := options.get("nested_strategy"):
                    handler = shared.strategies[strategy]()
                else:
                    handler = shared.get_handler_for_mimetype(
                        mime,
                        shared.make_file_storage(
                            archive.open(item),
                            os.path.basename(item),
                            mime,
                        ),
                    )
                    if not handler:
                        log.debug("Skip %s with MIMEType %s", item, mime)
                        continue

                yield {
                    "handler": handler,
                    "name": item,
                    "source": shared.make_file_storage(archive.open(item)),
                    "file_locator": file_locator,
                }

    def extract(
        self,
        source: shared.Storage,
        options: shared.StrategyOptions,
    ) -> Iterable[shared.Record]:
        for chunk in self.chunks(source, options):
            nested_options = shared.StrategyOptions(
                options,
                file_locator=chunk["file_locator"],
            )
            yield from chunk["handler"].extract(chunk["source"], nested_options)
