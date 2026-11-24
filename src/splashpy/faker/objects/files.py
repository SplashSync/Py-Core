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


"""Faker files: file & image fields download what they receive and store raw files.

When a file value is received, the faker downloads the file from Splash (``ReadFile``),
checks its checksum and stores the raw contents once, by md5 (see ``FakerStore``).
Objects only keep the name, the filename and the checksum: read values are rebuilt
from the stored file itself, never from what was received.

Stored files are published:

- to Splash, by path & checksum (``ReadFile``): path ``faker/files/<md5>``;
- over HTTP, for humans: ``<server path>/files/<md5>`` (see ``FakerHttpApp``).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, Final

from splashpy.core.context import RequestContext
from splashpy.faker.objects.base import StoredGroup
from splashpy.faker.store import FakerStore, StoredFile
from splashpy.fields import Files
from splashpy.objects import ObjectRequest

FILES_ROUTE: Final = "/files/"
"""HTTP route of faker files, after the server path."""

MD5: Final = re.compile(r"[a-f0-9]{32}")
"""Format of a file checksum."""


def public_url(ctx: RequestContext, md5: str) -> str | None:
    """Public URL of a stored file, from the host & path of the current request."""
    if not ctx.server_host:
        return None
    return f"{ctx.server_host}{(ctx.server_path or '').rstrip('/')}{FILES_ROUTE}{md5}"


class StoredFileGroup(StoredGroup):
    """Base of faker groups with file or image fields."""

    @classmethod
    def read_file(cls, req: ObjectRequest, field_id: str, image: bool = False) -> dict[str, Any] | None:
        """Rebuild a file value from the stored file."""
        record = cls.record(req)
        link = record.data.get(field_id)
        if not isinstance(link, Mapping) or record.store is None:
            return None
        stored = record.store.load_file(str(link.get("md5")))
        if stored is None:
            req.logger.warning(f"Faker file {link.get('md5')} is missing.")
            return None
        return cls._value(req.ctx, link, stored, image)

    @classmethod
    def write_file(cls, req: ObjectRequest, field_id: str, value: Any) -> bool:
        """Download a received file when not already stored, then keep a link to it."""
        if not value:
            return cls.write(req, field_id, None)
        md5 = value.get("md5") if isinstance(value, Mapping) else None
        path = (value.get("path") or value.get("file")) if isinstance(value, Mapping) else None
        store = cls.record(req).store
        if not isinstance(md5, str) or not MD5.fullmatch(md5) or not isinstance(path, str) or store is None:
            req.logger.error(f"Faker - Invalid file value for {field_id}.")
            return False
        if not store.has_file(md5) and not cls._download(req, store, path, md5):
            return False
        link = {"name": value.get("name"), "filename": value.get("filename"), "md5": md5}
        return cls.write(req, field_id, link)

    @classmethod
    def _download(cls, req: ObjectRequest, store: FakerStore, path: str, md5: str) -> bool:
        """Download a file from Splash and store it, when its checksum is right."""
        received = req.ctx.get_file(path, md5)
        raw = Files.decode_raw(received.get("raw")) if received else None
        if raw is None or Files.md5(raw) != md5:
            req.logger.error(f"Faker - Unable to download file {path} ({md5}).")
            return False
        store.save_file(raw)
        return True

    @staticmethod
    def _value(ctx: RequestContext, link: Mapping[str, Any], stored: StoredFile, image: bool) -> dict[str, Any]:
        """Build a file value: names from the link, everything else from the stored file."""
        value: dict[str, Any] = {
            "name": link.get("name"),
            "filename": link.get("filename"),
            "path": stored.path,
            "url": public_url(ctx, stored.md5),
        }
        if image:
            value.update(width=stored.width, height=stored.height)
        value.update(md5=stored.md5, size=stored.size)
        return value
