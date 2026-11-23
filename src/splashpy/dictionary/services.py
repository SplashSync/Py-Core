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

"""Names of the Splash SOAP services."""

from __future__ import annotations

from typing import Final


class SplServices:
    """Splash webservice names (mirror of Php-Core ``SplServices``)."""

    PING: Final = "Ping"
    """Availability check, never encrypted."""

    CONNECT: Final = "Connect"
    """Connection check, encrypted."""

    ADMIN: Final = "Admin"
    """Administrative requests (infos, objects list, selftest...)."""

    OBJECTS: Final = "Objects"
    """Objects requests (describe, list, get, set, delete, commit...)."""

    FILES: Final = "Files"
    """Files requests."""

    WIDGETS: Final = "Widgets"
    """Widgets requests."""

    ALL: Final = (PING, CONNECT, ADMIN, OBJECTS, FILES, WIDGETS)
    """Every known service."""
