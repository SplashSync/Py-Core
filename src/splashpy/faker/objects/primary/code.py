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

"""primary: the primary key and a flag."""

from __future__ import annotations

from typing import Any, Final

from splashpy.faker.objects.base import StoredGroup
from splashpy.fields import FieldsFactory, FieldType
from splashpy.objects import ObjectRequest, fields_group

PRIMARY: Final = "code"
"""Primary key field."""


@fields_group("code", priority=5)
class PrimaryCode(StoredGroup):
    """Primary key (required, listed) and an active flag."""

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare the primary key."""
        factory.create(FieldType.VARCHAR, PRIMARY, "Code").is_required().is_primary().is_listed()
        factory.micro_data("http://schema.org/Thing", "identifier")
        factory.create(FieldType.BOOL, "active", "Active")

    def get(self, req: ObjectRequest, field_id: str) -> Any:
        """Read the code or the flag."""
        return self.read(req, field_id)

    def set(self, req: ObjectRequest, field_id: str, value: Any) -> bool | None:
        """Write the code or the flag."""
        return self.write(req, field_id, value)
