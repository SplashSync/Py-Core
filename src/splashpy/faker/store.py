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

"""Faker storage: one JSON document per object, in a standard library SQLite database."""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Record:
    """A stored object: its id and its fields values, as received from Splash."""

    id: str
    """Object identifier."""

    data: dict[str, Any] = field(default_factory=dict)
    """Fields values, by field id (lists by list name)."""


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

    def create(self, object_type: str) -> Record:
        """Create an empty object."""
        with self._mutex, self._db:
            cursor = self._db.execute("INSERT INTO objects (type, data) VALUES (?, '{}')", (object_type,))
        return Record(str(cursor.lastrowid))

    def load(self, object_type: str, object_id: str) -> Record | None:
        """Load an object."""
        with self._mutex:
            row = self._db.execute(
                "SELECT data FROM objects WHERE type = ? AND id = ?", (object_type, _int(object_id))
            ).fetchone()
        return Record(str(object_id), json.loads(row[0])) if row else None

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
        return [Record(str(row[0]), json.loads(row[1])) for row in rows]


def _int(object_id: str) -> int:
    """Convert an object id, -1 when invalid (never found)."""
    try:
        return int(object_id)
    except (TypeError, ValueError):
        return -1
