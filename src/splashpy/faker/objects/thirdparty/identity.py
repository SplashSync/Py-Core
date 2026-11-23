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


"""ThirdParty: identity (name, person, civility, web)."""

from __future__ import annotations

from typing import Any, Final

from splashpy.contracts import default_catalog
from splashpy.faker.objects.base import TemplatedGroup
from splashpy.fields import FieldsFactory
from splashpy.objects import ObjectRequest, fields_group

CIVILITY: Final = "Splash.Templates.ThirdParty.Profile.CivilityType"
"""Civility template: its choices give the civility names."""


TEMPLATES: Final = {
    "name": "Splash.Templates.ThirdParty.Core.Name",
    "email": "Splash.Templates.ThirdParty.Core.Email",
    "firstname": "Splash.Templates.Address.Contact.Firstname",
    "lastname": "Splash.Templates.Address.Contact.Lastname",
    "phone": "Splash.Templates.ThirdParty.Core.Phone",
    "mobile": "Splash.Templates.ThirdParty.Core.MobilePhone",
    "civility": CIVILITY,
    "civility_name": "Splash.Templates.ThirdParty.Profile.CivilityName",
    "website": "Splash.Templates.ThirdParty.Profile.Website",
}
"""Fields: field id => template code."""


@fields_group("identity", priority=10)
class ThirdPartyIdentity(TemplatedGroup):
    """Name (required), email, person names, phones, civility and website."""

    templates = TEMPLATES

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare identity fields."""
        self.build_templates(factory)

    def get(self, req: ObjectRequest, field_id: str) -> Any:
        """Read a field; the civility name is computed from the civility."""
        if field_id == "civility_name":
            choices = default_catalog().template(CIVILITY)["config"].get("choices") or {}
            return choices.get(self.read(req, "civility"))
        return self.read(req, field_id)
