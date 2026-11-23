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


"""simple: fields built from contracts templates (Php-Scopes)."""

from __future__ import annotations

from typing import Final

from splashpy.faker.objects.base import TemplatedGroup
from splashpy.fields import FieldsFactory
from splashpy.objects import ObjectRequest, fields_group

GROUP: Final = "Templates"
"""Fields group label."""

TEMPLATES: Final = {
    "contact_civility": "Splash.Templates.ThirdParty.Profile.CivilityType",
    "contact_email": "Splash.Templates.ThirdParty.Core.Email",
    "contact_phone": "Splash.Templates.ThirdParty.Core.Phone",
    "contact_website": "Splash.Templates.ThirdParty.Profile.Website",
    "contact_zip": "Splash.Templates.Address.PostalAddress.PostalCode",
}
"""Templated fields: field id => template code."""


@fields_group("templates", priority=45, after=("basic",))
class SimpleTemplates(TemplatedGroup):
    """Fields defined by templates: type, metadata, choices and options come from the catalog."""

    templates = TEMPLATES
    label = GROUP

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare templated fields."""
        self.build_templates(factory)
