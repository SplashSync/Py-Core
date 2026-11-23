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

"""Commit events: local changes notified to Splash."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CommitEvent:
    """A local change (mirror of Php-Core ``CommitEvent::toArray()``)."""

    type: str
    """Splash object type."""

    ids: tuple[str, ...]
    """Identifiers of the changed objects."""

    action: str
    """``create``, ``update``, ``delete`` or ``rename`` (see ``SplOperations``)."""

    user: str = ""
    """User who made the change, for Splash logs."""

    comment: str = ""
    """Comment, for Splash logs."""

    sent: bool = False
    """True when the event was sent to Splash, False when skipped."""

    @staticmethod
    def ids_of(object_ids: str | int | Sequence[str | int]) -> tuple[str, ...]:
        """Normalize one or many ids to strings."""
        if isinstance(object_ids, (str, int)):
            return (str(object_ids),)
        return tuple(str(object_id) for object_id in object_ids)

    def params(self) -> dict[str, Any]:
        """Parameters of the ``Commit`` task."""
        return {
            "type": self.type,
            "id": list(self.ids),
            "action": self.action,
            "user": self.user,
            "comment": self.comment,
        }
