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


"""ThirdParty: postal address, contact and identifiers."""

from __future__ import annotations

from typing import Any, Final

from splashpy.faker.objects.base import TemplatedGroup
from splashpy.fields import FieldsFactory
from splashpy.objects import ObjectRequest, fields_group

COMPUTED: Final = {"region_name": "region", "country_name": "country"}
"""Read-only fields, computed from another field."""


TEMPLATES: Final = {
    "alternate_name": "Splash.Templates.Address.Contact.AlternateName",
    "fax": "Splash.Templates.Address.Contact.Fax",
    "street": "Splash.Templates.Address.PostalAddress.StreetAddress",
    "po_box": "Splash.Templates.Address.PostalAddress.PostOfficeBoxNumber",
    "extended": "Splash.Templates.Address.PostalAddress.ExtendedAddress",
    "zip": "Splash.Templates.Address.PostalAddress.PostalCode",
    "city": "Splash.Templates.Address.PostalAddress.Locality",
    "region": "Splash.Templates.Address.PostalAddress.RegionCode",
    "region_name": "Splash.Templates.Address.PostalAddress.RegionName",
    "country": "Splash.Templates.Address.PostalAddress.CountryCode",
    "country_name": "Splash.Templates.Address.PostalAddress.CountryName",
    "duns": "Splash.Templates.Address.Identifiers.Duns",
    "tax_id": "Splash.Templates.Address.Identifiers.TaxId",
    "vat_id": "Splash.Templates.Address.Identifiers.VatId",
}
"""Fields: field id => template code."""


@fields_group("address", priority=20, after=("identity",))
class ThirdPartyAddress(TemplatedGroup):
    """Address contact, postal address and identifiers.

    Templates sharing the metadata of an identity field (contact name, email & phone) are not
    exposed twice: the identity field satisfies both constraints, and the validator requires a
    single field per metadata.
    """

    templates = TEMPLATES

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare address fields."""
        self.build_templates(factory)

    def get(self, req: ObjectRequest, field_id: str) -> Any:
        """Read a field; region & country names are their codes (no lookup in the faker)."""
        return self.read(req, COMPUTED.get(field_id, field_id))
