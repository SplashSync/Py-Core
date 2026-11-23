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

"""Faker storage, in a standard library SQLite database.

- ``objects``: one JSON document per object;
- ``files``: raw files (files and images), stored once by md5 checksum, with their
  information (size, mime type, image dimensions). Objects only keep the checksum.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass, field
from typing import Any, Final

from splashpy.fields import Files, Images


@dataclass
class Record:
    """A stored object: its id and its fields values, as received from Splash."""

    id: str
    """Object identifier."""

    data: dict[str, Any] = field(default_factory=dict)
    """Fields values, by field id (lists by list name)."""

    store: FakerStore | None = field(default=None, repr=False, compare=False)
    """Store the object was loaded from (gives access to stored files)."""


FILES_PATH: Final = "faker/files/"
"""Prefix of stored files paths, given to Splash to read them back (path & checksum)."""


@dataclass(frozen=True)
class StoredFile:
    """A raw file and its information, read from its contents."""

    md5: str
    """Checksum of the contents: the file identifier."""

    raw: bytes = field(repr=False)
    """Contents."""

    size: int
    """Size, in bytes."""

    mime: str
    """Mime type, detected from contents."""

    width: int | None = None
    """Image width, None when not an image."""

    height: int | None = None
    """Image height, None when not an image."""

    @property
    def path(self) -> str:
        """Path of the file, as published to Splash."""
        return f"{FILES_PATH}{self.md5}"

    @staticmethod
    def from_raw(raw: bytes) -> StoredFile:
        """Read the information of a raw file."""
        kind = Images.kind(raw)
        dims = Images.dimensions(raw) if kind else None
        if kind:
            mime = f"image/{kind}"
        elif raw.startswith(b"%PDF"):
            mime = "application/pdf"
        else:
            mime = "application/octet-stream"
        return StoredFile(Files.md5(raw), raw, len(raw), mime, dims[0] if dims else None, dims[1] if dims else None)


class FakerStore:
    """Thread-safe documents store. In memory by default: empty at each start."""

    def __init__(self, path: str = ":memory:") -> None:
        """Open (and create) the database."""
        self._mutex = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        with self._mutex, self._db:
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS objects ("
                " id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, data TEXT NOT NULL)"
            )
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS files ("
                " md5 TEXT PRIMARY KEY, raw BLOB NOT NULL, size INTEGER NOT NULL, mime TEXT NOT NULL,"
                " width INTEGER, height INTEGER)"
            )

    def create(self, object_type: str) -> Record:
        """Create an empty object."""
        with self._mutex, self._db:
            cursor = self._db.execute("INSERT INTO objects (type, data) VALUES (?, '{}')", (object_type,))
        return Record(str(cursor.lastrowid), store=self)

    def load(self, object_type: str, object_id: str) -> Record | None:
        """Load an object."""
        with self._mutex:
            row = self._db.execute(
                "SELECT data FROM objects WHERE type = ? AND id = ?", (object_type, _int(object_id))
            ).fetchone()
        return Record(str(object_id), json.loads(row[0]), self) if row else None

    def save(self, object_type: str, record: Record) -> bool:
        """Save an object."""
        with self._mutex, self._db:
            cursor = self._db.execute(
                "UPDATE objects SET data = ? WHERE type = ? AND id = ?",
                (json.dumps(record.data), object_type, _int(record.id)),
            )
        return cursor.rowcount == 1

    def delete(self, object_type: str, object_id: str) -> None:
        """Delete an object (missing objects are ignored)."""
        with self._mutex, self._db:
            self._db.execute("DELETE FROM objects WHERE type = ? AND id = ?", (object_type, _int(object_id)))

    def all(self, object_type: str) -> list[Record]:
        """Get every object of a type, by id."""
        with self._mutex:
            rows = self._db.execute(
                "SELECT id, data FROM objects WHERE type = ? ORDER BY id", (object_type,)
            ).fetchall()
        return [Record(str(row[0]), json.loads(row[1]), self) for row in rows]

    def save_file(self, raw: bytes) -> StoredFile:
        """Store a raw file (once: the same contents are never stored twice)."""
        stored = StoredFile.from_raw(raw)
        with self._mutex, self._db:
            self._db.execute(
                "INSERT OR IGNORE INTO files (md5, raw, size, mime, width, height) VALUES (?, ?, ?, ?, ?, ?)",
                (stored.md5, stored.raw, stored.size, stored.mime, stored.width, stored.height),
            )
        return stored

    def load_file(self, md5: str) -> StoredFile | None:
        """Load a raw file by checksum."""
        with self._mutex:
            row = self._db.execute(
                "SELECT md5, raw, size, mime, width, height FROM files WHERE md5 = ?", (md5,)
            ).fetchone()
        return StoredFile(row[0], bytes(row[1]), row[2], row[3], row[4], row[5]) if row else None

    def read_file(self, path: str, md5: str) -> dict[str, Any] | None:
        """Answer a Splash ``ReadFile``: a stored file, when path & checksum match."""
        stored = self.load_file(md5)
        if stored is None or stored.path != path:
            return None
        return Files.read(stored.md5, stored.raw)

    def has_file(self, md5: str) -> bool:
        """Check if a raw file is stored."""
        with self._mutex:
            row = self._db.execute("SELECT 1 FROM files WHERE md5 = ?", (md5,)).fetchone()
        return row is not None


def _int(object_id: str) -> int:
    """Convert an object id, -1 when invalid (never found)."""
    try:
        return int(object_id)
    except (TypeError, ValueError):
        return -1
