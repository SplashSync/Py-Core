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

"""short: one varchar and one bool, only to check the synchronization works."""

from __future__ import annotations

from splashpy.faker.objects.base import FakerObject
from splashpy.faker.objects.core import CoreName
from splashpy.objects.discovery import discover_groups


class Short(FakerObject):
    """Smallest faker object."""

    type = "short"
    name = "Short"
    description = "Faker object with two fields, to check the synchronization works"
    icon = "fa fa-minus"
    priority = 10
    groups = (CoreName, *discover_groups(__name__))
