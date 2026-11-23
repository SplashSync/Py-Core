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

"""simple: advanced field types."""

from __future__ import annotations

from typing import Any, Final

from splashpy.faker.objects.base import StoredGroup
from splashpy.fields import FieldsFactory, FieldType
from splashpy.objects import ObjectRequest, fields_group

GROUP: Final = "Advanced Types"
"""Fields group label."""

TYPES: Final = (FieldType.LANG, FieldType.COUNTRY, FieldType.STATE, FieldType.CURRENCY, FieldType.PRICE)
"""One field of each advanced type, named after its type."""


@fields_group("advanced", priority=30, after=("basic",))
class SimpleAdvanced(StoredGroup):
    """Codes, price, inlines with and without choices, link to a short object."""

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare advanced fields."""
        for field_type in TYPES:
            factory.create(field_type, field_type, field_type.capitalize()).group(GROUP)
        factory.create(FieldType.INLINE, "tags", "Tags").group(GROUP)
        factory.create(FieldType.INLINE, "colors", "Colors").group(GROUP)
        factory.add_choices({"red": "Red", "green": "Green", "blue": "Blue"})
        factory.create(FieldType.object_id("short"), "short", "Short").group(GROUP)

    def get(self, req: ObjectRequest, field_id: str) -> Any:
        """Read advanced fields."""
        return self.read(req, field_id)

    def set(self, req: ObjectRequest, field_id: str, value: Any) -> bool | None:
        """Write advanced fields."""
        return self.write(req, field_id, value)
