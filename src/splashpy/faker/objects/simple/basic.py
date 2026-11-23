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

"""simple: basic field types."""

from __future__ import annotations

from typing import Any, Final

from splashpy.faker.objects.base import StoredGroup
from splashpy.fields import FieldsFactory, FieldType
from splashpy.objects import ObjectRequest, fields_group

GROUP: Final = "Basic Types"
"""Fields group label."""

TYPES: Final = (
    FieldType.TEXT,
    FieldType.BOOL,
    FieldType.INT,
    FieldType.DOUBLE,
    FieldType.DATE,
    FieldType.DATETIME,
    FieldType.EMAIL,
    FieldType.PHONE,
    FieldType.URL,
)
"""One field of each basic type, named after its type."""

WRITE_ONLY: Final = "secret"
"""Write only field: never returned on read."""


@fields_group("basic", priority=20, after=("core",))
class SimpleBasic(StoredGroup):
    """Basic types, choices, read only and write only fields."""

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare basic fields."""
        for field_type in TYPES:
            factory.create(field_type, field_type, field_type.capitalize()).group(GROUP)
        factory.create(FieldType.VARCHAR, "status", "Status").group(GROUP)
        factory.add_choices({"draft": "Draft", "validated": "Validated", "done": "Done"})
        factory.create(FieldType.VARCHAR, "notes", "Notes (read only)").group(GROUP).is_read_only()
        factory.create(FieldType.VARCHAR, WRITE_ONLY, "Secret (write only)").group(GROUP).is_write_only()

    def get(self, req: ObjectRequest, field_id: str) -> Any:
        """Read basic fields (never the write only one)."""
        return None if field_id == WRITE_ONLY else self.read(req, field_id)

    def set(self, req: ObjectRequest, field_id: str, value: Any) -> bool | None:
        """Write basic fields."""
        return self.write(req, field_id, value)
