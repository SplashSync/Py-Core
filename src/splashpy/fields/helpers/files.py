#
#  This file is part of SplashSync Project.
#
#  Copyright (C) Splash Sync  <www.splashsync.com>
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  For the full copyright and license information, please view the LICENSE
#  file that was distributed with this source code.
#


"""Files values (mirror of Php-Core ``FilesHelper``)."""

from __future__ import annotations

import base64
import hashlib
from typing import Any


class Files:
    """Encode files as Splash file values, and read files for the Files service."""

    @staticmethod
    def md5(raw: bytes) -> str:
        """Hexadecimal md5 of contents (Splash file identity, not a security hash)."""
        return hashlib.md5(raw, usedforsecurity=False).hexdigest()

    @staticmethod
    def encode(name: str, filename: str, path: str, raw: bytes, url: str | None = None) -> dict[str, Any] | None:
        """Build a file value from its contents.

        :param path: identifier of the file on this node, given back by Splash to read it.
        """
        if not name or not filename or not path:
            return None
        return {
            "name": name,
            "filename": filename,
            "path": path,
            "url": url,
            "md5": Files.md5(raw),
            "size": len(raw),
        }

    @staticmethod
    def read(filename: str, raw: bytes) -> dict[str, Any]:
        """Build a ``ReadFile`` response: filename, md5, size and base64 contents."""
        return {
            "filename": filename,
            "md5": Files.md5(raw),
            "size": len(raw),
            "raw": base64.b64encode(raw).decode("ascii"),
        }

    @staticmethod
    def decode_raw(value: Any) -> bytes | None:
        """Decode base64 contents received from Splash."""
        if not isinstance(value, str) or not value:
            return None
        try:
            return base64.b64decode(value, validate=True)
        except ValueError:
            return None
