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


"""List fields identifiers (mirror of Php-Core ``ListsHelper``)."""

from __future__ import annotations

from splashpy.dictionary import SplFormats


class Lists:
    """List fields: ``field@list`` identifiers."""

    @staticmethod
    def encode(list_name: str, field_name: str) -> str | None:
        """Build ``field@list``, None when a part is empty."""
        if not list_name or not field_name:
            return None
        return f"{field_name}{SplFormats.LIST_SPLIT}{list_name}"

    @staticmethod
    def explode(field_id: str | None) -> tuple[str, str] | None:
        """Split ``field@list`` into ``(field, list)``, None when not a list field."""
        if not field_id:
            return None
        parts = field_id.split(SplFormats.LIST_SPLIT)
        if len(parts) != 2:
            return None
        return parts[0], parts[1]

    @staticmethod
    def is_list(field_id: str | None) -> bool:
        """Check if an identifier (or a type) is a list one."""
        return Lists.explode(field_id) is not None

    @staticmethod
    def field_name(field_id: str | None) -> str | None:
        """Get the field part of ``field@list``."""
        parts = Lists.explode(field_id)
        return parts[0] if parts else None

    @staticmethod
    def list_name(field_id: str | None) -> str | None:
        """Get the list part of ``field@list``."""
        parts = Lists.explode(field_id)
        return parts[1] if parts else None
