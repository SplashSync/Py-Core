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


"""Images values (mirror of Php-Core ``ImagesHelper``).

Image types and dimensions are read from file headers: no ``imghdr`` (removed in
Python 3.13), no Pillow.
"""

from __future__ import annotations

import struct
from typing import Any

from splashpy.fields.helpers.files import Files

_PNG = b"\x89PNG\r\n\x1a\n"
"""PNG signature."""


class Images(Files):
    """Encode images: file keys plus width & height, read from headers."""

    @staticmethod
    def encode_image(name: str, filename: str, path: str, raw: bytes, url: str | None = None) -> dict[str, Any] | None:
        """Build an image value, None when contents are not a supported image."""
        dims = Images.dimensions(raw)
        if dims is None or not name or not filename or not path:
            return None
        return {
            "name": name,
            "filename": filename,
            "path": path,
            "url": url,
            "width": dims[0],
            "height": dims[1],
            "md5": Files.md5(raw),
            "size": len(raw),
        }

    @staticmethod
    def kind(raw: bytes) -> str | None:
        """Detect the image type: png, jpeg, gif, webp or bmp."""
        if raw.startswith(_PNG):
            return "png"
        if raw.startswith(b"\xff\xd8"):
            return "jpeg"
        if raw[:6] in (b"GIF87a", b"GIF89a"):
            return "gif"
        if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
            return "webp"
        if raw.startswith(b"BM"):
            return "bmp"
        return None

    @staticmethod
    def dimensions(raw: bytes) -> tuple[int, int] | None:
        """Read the image width & height from its header, None when unknown."""
        try:
            return _DIMENSIONS[Images.kind(raw) or ""](raw)
        except (KeyError, struct.error, IndexError, ValueError):
            return None


def _png(raw: bytes) -> tuple[int, int]:
    """PNG: IHDR chunk."""
    width, height = struct.unpack(">II", raw[16:24])
    return width, height


def _gif(raw: bytes) -> tuple[int, int]:
    """GIF: logical screen descriptor."""
    width, height = struct.unpack("<HH", raw[6:10])
    return width, height


def _bmp(raw: bytes) -> tuple[int, int]:
    """BMP: info header."""
    width, height = struct.unpack("<ii", raw[18:26])
    return width, abs(height)


def _webp(raw: bytes) -> tuple[int, int]:
    """WebP: VP8, VP8L or VP8X chunks."""
    chunk = raw[12:16]
    if chunk == b"VP8 ":
        width, height = struct.unpack("<HH", raw[26:30])
        return width & 0x3FFF, height & 0x3FFF
    if chunk == b"VP8L":
        bits = int.from_bytes(raw[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if chunk == b"VP8X":
        return int.from_bytes(raw[24:27], "little") + 1, int.from_bytes(raw[27:30], "little") + 1
    raise ValueError("Unknown WebP chunk")


def _jpeg(raw: bytes) -> tuple[int, int]:
    """JPEG: first start of frame marker."""
    offset = 2
    while offset < len(raw):
        while raw[offset] != 0xFF:
            offset += 1
        marker = raw[offset + 1]
        offset += 2
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            continue
        length = struct.unpack(">H", raw[offset : offset + 2])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height, width = struct.unpack(">HH", raw[offset + 3 : offset + 7])
            return width, height
        offset += length
    raise ValueError("No JPEG frame")


_DIMENSIONS = {"png": _png, "gif": _gif, "bmp": _bmp, "webp": _webp, "jpeg": _jpeg}
"""Dimension readers by image type."""
