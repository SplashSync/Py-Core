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

"""Splash protocol dictionaries: every reusable constant lives here, never hardcoded elsewhere."""

from __future__ import annotations

from splashpy.dictionary.contracts import SplContracts
from splashpy.dictionary.definition import SplDefinition
from splashpy.dictionary.formats import SplFormats
from splashpy.dictionary.methods import (
    SplAdminMethods,
    SplFilesMethods,
    SplObjectMethods,
    SplWidgetsMethods,
)
from splashpy.dictionary.operations import SplOperations
from splashpy.dictionary.services import SplServices

__all__ = [
    "SplAdminMethods",
    "SplContracts",
    "SplDefinition",
    "SplFilesMethods",
    "SplFormats",
    "SplObjectMethods",
    "SplOperations",
    "SplServices",
    "SplWidgetsMethods",
]
