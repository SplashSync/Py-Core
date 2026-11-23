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

"""Faker objects, aligned on the Php-Core faker types. Values are stored and returned as received.

Each object is a package: its main class (CRUD) in ``__init__``, one module per part
(fields group: build, read, write), parts included with ``discover_groups()``.
"""

from __future__ import annotations

from splashpy.faker.objects.base import FakerObject, StoredGroup
from splashpy.faker.objects.file import File
from splashpy.faker.objects.image import Image
from splashpy.faker.objects.list import List
from splashpy.faker.objects.primary import Primary
from splashpy.faker.objects.short import Short
from splashpy.faker.objects.simple import Simple

OBJECTS: tuple[type[FakerObject], ...] = (Short, Simple, List, Primary, Image, File)
"""Every faker object."""

__all__ = ["OBJECTS", "FakerObject", "File", "Image", "List", "Primary", "Short", "Simple", "StoredGroup"]
