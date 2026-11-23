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

"""Names of the tasks executed by each Splash service."""

from __future__ import annotations

from typing import Final


class SplAdminMethods:
    """Tasks of the Admin service."""

    INFOS: Final = "infos"
    """Read client information."""

    OBJECTS: Final = "objects"
    """Read available object types."""

    SELF_TEST: Final = "selftest"
    """Run the client self test."""

    WIDGETS: Final = "widgets"
    """Read available widget types."""

    ALL: Final = (INFOS, OBJECTS, SELF_TEST, WIDGETS)
    """Every Admin task."""


class SplObjectMethods:
    """Tasks of the Objects service."""

    OBJECTS: Final = "Objects"
    """Read available object types."""

    DESC: Final = "Description"
    """Read an object description."""

    FIELDS: Final = "Fields"
    """Read an object fields definitions."""

    LIST: Final = "ObjectsList"
    """List objects."""

    IDENTIFY: Final = "Identify"
    """Identify an object by its primary keys."""

    GET: Final = "Get"
    """Read object data."""

    SET: Final = "Set"
    """Write object data."""

    DEL: Final = "Delete"
    """Delete an object."""

    COMMIT: Final = "Commit"
    """Notify Splash of a local change (outgoing only)."""

    ALL: Final = (OBJECTS, DESC, FIELDS, LIST, IDENTIFY, GET, SET, DEL, COMMIT)
    """Every Objects task."""


class SplFilesMethods:
    """Tasks of the Files service."""

    EXISTS: Final = "isFile"
    """Check if a file exists."""

    GET: Final = "ReadFile"
    """Read a file."""

    SET: Final = "SetFile"
    """Write a file."""

    DEL: Final = "DeleteFile"
    """Delete a file."""

    ALL: Final = (EXISTS, GET, SET, DEL)
    """Every Files task."""


class SplWidgetsMethods:
    """Tasks of the Widgets service."""

    LIST: Final = "WidgetsList"
    """Read available widget types."""

    DEFINITION: Final = "Description"
    """Read a widget definition."""

    GET: Final = "Get"
    """Read widget contents."""

    ALL: Final = (LIST, DEFINITION, GET)
    """Every Widgets task."""
