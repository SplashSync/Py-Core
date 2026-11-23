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

"""file: a document."""

from __future__ import annotations

from typing import Any

from splashpy.faker.objects.files import StoredFileGroup
from splashpy.fields import FieldsFactory, FieldType
from splashpy.objects import ObjectRequest, fields_group


@fields_group("document", priority=50, after=("core",))
class FileDocument(StoredFileGroup):
    """One file, downloaded and stored by checksum."""

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare the file."""
        factory.create(FieldType.FILE, "document", "Document")

    def get(self, req: ObjectRequest, field_id: str) -> Any:
        """Read the file."""
        return self.read_file(req, field_id)

    def set(self, req: ObjectRequest, field_id: str, value: Any) -> bool | None:
        """Write the file."""
        return self.write_file(req, field_id, value)
