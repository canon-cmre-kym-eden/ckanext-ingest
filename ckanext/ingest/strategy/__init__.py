from __future__ import annotations

from typing import Any, Optional
from .base import Handler, PackageRecord, ResourceRecord

__all__ = ["PackageRecord", "ResourceRecord", "Handler", "get_handler"]


def get_handler(mime: Any) -> Optional[Handler]:
    from .zip import ZipStrategy
    from .xlsx import ExcelStrategy

    if mime == "application/zip":
        return Handler(ZipStrategy())
    if mime == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        return Handler(ExcelStrategy())
