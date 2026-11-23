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

"""image: a name and two images."""

from __future__ import annotations

from splashpy.faker.objects.base import FakerObject
from splashpy.faker.objects.core import CoreName
from splashpy.objects.discovery import discover_groups


class Image(FakerObject):
    """Faker object with images."""

    type = "image"
    name = "Image"
    description = "Faker object with images"
    icon = "fa fa-image"
    priority = 50
    groups = (CoreName, *discover_groups(__name__))
