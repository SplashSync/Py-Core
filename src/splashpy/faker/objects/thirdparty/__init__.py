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


"""ThirdParty: a real Splash object type, built from contracts templates, declaring a scope.

Every field comes from a template of the ``Splash.Scopes.ThirdParty.Provider`` scope, so the
Toolkit validator checks the scope constraints (and its functional tests) against this object.
"""

from __future__ import annotations

from typing import Final

from splashpy.faker.objects.base import FakerObject
from splashpy.objects.discovery import discover_groups

SCOPE: Final = "Splash.Scopes.ThirdParty.Provider"
"""Scope declared by the faker for this object."""


class ThirdParty(FakerObject):
    """Faker third party (customer, company), defined by templates."""

    type = "ThirdParty"
    name = "ThirdParty"
    description = "Faker third party, built from contracts templates"
    icon = "fa fa-user"
    priority = 70
    listed_fields = ("name", "email")
    groups = discover_groups(__name__)
