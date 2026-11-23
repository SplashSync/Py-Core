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

"""simple: every field type but images & files."""

from __future__ import annotations

from splashpy.faker.objects.base import FakerObject
from splashpy.faker.objects.core import CoreName
from splashpy.faker.objects.simple.basic import SimpleBasic
from splashpy.objects.discovery import discover_groups


class Simple(FakerObject):
    """Every field type but images & files: basic, advanced and translated fields."""

    type = "simple"
    name = "Simple"
    description = "Faker object with every field type but images & files"
    icon = "fa fa-cube"
    priority = 20
    groups = (CoreName, *discover_groups(__name__))


__all__ = ["Simple", "SimpleBasic"]
