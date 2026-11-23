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

"""image: picture and thumbnail."""

from __future__ import annotations

from typing import Any

from splashpy.faker.objects.files import StoredFileGroup
from splashpy.fields import FieldsFactory, FieldType
from splashpy.objects import ObjectRequest, fields_group


@fields_group("pictures", priority=50, after=("core",))
class ImagePictures(StoredFileGroup):
    """Two images, downloaded and stored by checksum."""

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare images."""
        factory.create(FieldType.IMAGE, "picture", "Picture")
        factory.create(FieldType.IMAGE, "thumbnail", "Thumbnail")

    def get(self, req: ObjectRequest, field_id: str) -> Any:
        """Read an image."""
        return self.read_file(req, field_id, image=True)

    def set(self, req: ObjectRequest, field_id: str, value: Any) -> bool | None:
        """Write an image."""
        return self.write_file(req, field_id, value)
