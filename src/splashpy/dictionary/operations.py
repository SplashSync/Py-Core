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

"""Commit actions sent to the Splash server."""

from __future__ import annotations

from typing import Final


class SplOperations:
    """Commit actions (mirror of Php-Core ``SplOperations``)."""

    CREATE: Final = "create"
    """Object locally created."""

    UPDATE: Final = "update"
    """Object locally modified."""

    DELETE: Final = "delete"
    """Object locally deleted."""

    RENAME: Final = "rename"
    """Object identifier changed."""

    ALL: Final = (CREATE, UPDATE, DELETE, RENAME)
    """Every commit action."""
