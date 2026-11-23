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

"""primary: the ONLY faker object with a primary key."""

from __future__ import annotations

from collections.abc import Mapping

from splashpy.core.context import RequestContext
from splashpy.faker.objects.base import FakerObject
from splashpy.faker.objects.core import CoreName
from splashpy.faker.objects.primary.code import PRIMARY
from splashpy.objects.discovery import discover_groups


class Primary(FakerObject):
    """Faker object identified by a primary key."""

    type = "primary"
    name = "Primary"
    description = "Faker object identified by a primary key"
    icon = "fa fa-key"
    priority = 40
    listed_fields = (PRIMARY, "name")
    groups = (CoreName, *discover_groups(__name__))

    def get_by_primary(self, ctx: RequestContext, keys: Mapping[str, str]) -> str | None:
        """Find the only record with this code."""
        value = keys.get(PRIMARY)
        if not value:
            return None
        matches = [record.id for record in self.store.all(self.object_type()) if record.data.get(PRIMARY) == value]
        return matches[0] if len(matches) == 1 else None
