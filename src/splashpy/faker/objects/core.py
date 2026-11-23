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

"""Shared part of every faker object: a required & listed name."""

from __future__ import annotations

from typing import Any

from splashpy.faker.objects.base import StoredGroup
from splashpy.fields import FieldsFactory, FieldType
from splashpy.objects import ObjectRequest, fields_group


@fields_group("core", priority=10)
class CoreName(StoredGroup):
    """A required & listed name."""

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare the name."""
        factory.create(FieldType.VARCHAR, "name", "Name").is_required().is_listed()
        factory.micro_data("http://schema.org/Thing", "name")

    def get(self, req: ObjectRequest, field_id: str) -> Any:
        """Read the name."""
        return self.read(req, field_id)

    def set(self, req: ObjectRequest, field_id: str, value: Any) -> bool | None:
        """Write the name."""
        return self.write(req, field_id, value)
