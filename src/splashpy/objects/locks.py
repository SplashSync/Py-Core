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

"""Objects locks: while Splash writes an object, its local changes must not be committed back.

Locks are keyed by object type AND id (1.0 shared them between every type), and shared
by every thread of one client: the host application commits from its own threads.
"""

from __future__ import annotations

import threading
from typing import Final

NEW: Final = "new"
"""Lock key of an object being created."""


class Locks:
    """Thread-safe set of locked objects."""

    def __init__(self) -> None:
        """Create an empty set of locks."""
        self._locks: set[tuple[str, str]] = set()
        self._mutex = threading.Lock()

    def lock(self, object_type: str, object_id: str | None) -> None:
        """Lock an object (``None`` / empty id: the object being created)."""
        with self._mutex:
            self._locks.add((object_type, self._key(object_id)))

    def unlock(self, object_type: str, object_id: str | None) -> None:
        """Release an object."""
        with self._mutex:
            self._locks.discard((object_type, self._key(object_id)))

    def is_locked(self, object_type: str, object_id: str | None = None) -> bool:
        """Check if an object is locked."""
        with self._mutex:
            return (object_type, self._key(object_id)) in self._locks

    @staticmethod
    def _key(object_id: str | None) -> str:
        """Lock key of an id."""
        return str(object_id) if object_id not in (None, "", "0") else NEW
