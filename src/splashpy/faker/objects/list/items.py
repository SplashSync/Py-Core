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

"""list: items, a list of bool, varchar, double & price."""

from __future__ import annotations

from typing import Any, Final

from splashpy.faker.objects.base import StoredGroup
from splashpy.fields import FieldsFactory, FieldType
from splashpy.objects import ObjectRequest, fields_group

LIST: Final = "items"
"""List name."""


@fields_group("items", priority=50, after=("core",))
class ListItems(StoredGroup):
    """Items of basic types."""

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare list fields."""
        factory.create(FieldType.BOOL, "enabled", "Item Enabled").in_list(LIST).group("Items")
        factory.create(FieldType.VARCHAR, "label", "Item Label").in_list(LIST).group("Items")
        factory.create(FieldType.DOUBLE, "qty", "Item Quantity").in_list(LIST).group("Items")
        factory.create(FieldType.PRICE, "price", "Item Price").in_list(LIST).group("Items")

    def get(self, req: ObjectRequest, field_id: str) -> Any:
        """Read one field of every item."""
        return self.read(req, field_id)

    def set(self, req: ObjectRequest, field_id: str, value: Any) -> bool | None:
        """Write the whole list (``field_id`` is the list name)."""
        return self.write(req, field_id, value)
