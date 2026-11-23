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

"""State of one object operation (describe, get, set...): never stored on shared objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from splashpy.core.context import RequestContext
from splashpy.core.logger import Logger

MAIN_FLAG = "object"
"""Name of the main update flag."""


@dataclass
class ObjectRequest:
    """One operation on one object: what fields groups receive.

    It carries the request context, the loaded native object and the update flags.
    """

    ctx: RequestContext
    """Context of the Splash request."""

    object_type: str
    """Splash object type."""

    object_id: str | None = None
    """Identifier of the object (None while creating)."""

    object: Any = None
    """The native object, as returned by ``load()`` or ``create()``."""

    inputs: dict[str, Any] = field(default_factory=dict)
    """Values received for a ``Set`` (``""`` already converted to None)."""

    stash: dict[str, Any] = field(default_factory=dict)
    """Free storage shared by groups during one operation (e.g. values for ``create()``)."""

    _flags: dict[str, bool] = field(default_factory=dict)
    """Update flags."""

    @property
    def logger(self) -> Logger:
        """Logger of the Splash request."""
        return self.ctx.logger

    @property
    def is_new(self) -> bool:
        """True while creating the object."""
        return self.object_id is None

    def need_update(self, flag: str = MAIN_FLAG) -> None:
        """Mark the object (or a custom part) as changed."""
        self._flags[flag or MAIN_FLAG] = True

    def is_to_update(self, flag: str = MAIN_FLAG) -> bool:
        """Check if the object (or a custom part) changed."""
        return self._flags.get(flag or MAIN_FLAG, False)

    def set_updated(self, flag: str = MAIN_FLAG) -> None:
        """Clear a change flag."""
        self._flags.pop(flag or MAIN_FLAG, None)
