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


"""Object identifiers (mirror of Php-Core ``ObjectsHelper``)."""

from __future__ import annotations

from splashpy.dictionary import SplFormats


class ObjectIds:
    """Object identifiers: ``id::Type``."""

    @staticmethod
    def encode(object_type: str, object_id: str | int | None) -> str | None:
        """Build ``id::Type``, None when a part is empty."""
        if not object_type or object_id is None or object_id == "":
            return None
        return f"{object_id}{SplFormats.ID_SPLIT}{object_type}"

    @staticmethod
    def explode(value: str | None) -> tuple[str, str] | None:
        """Split ``id::Type`` into ``(id, Type)``, None when invalid."""
        if not value:
            return None
        parts = value.split(SplFormats.ID_SPLIT)
        if len(parts) != 2:
            return None
        return parts[0], parts[1]

    @staticmethod
    def id(value: str | None) -> str | None:
        """Get the id part of ``id::Type``."""
        parts = ObjectIds.explode(value)
        return parts[0] if parts else None

    @staticmethod
    def type(value: str | None) -> str | None:
        """Get the type part of ``id::Type``."""
        parts = ObjectIds.explode(value)
        return parts[1] if parts else None
