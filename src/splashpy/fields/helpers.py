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

"""Field values helpers: lists, object ids, inline lists, dates (mirror of Php-Core helpers)."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from typing import Any, Final

LIST_SPLIT: Final = "@"
"""Separator of list fields: ``field@list``."""

ID_SPLIT: Final = "::"
"""Separator of object ids: ``id::Type``."""

DATE_FORMAT: Final = "%Y-%m-%d"
"""Splash date format."""

DATETIME_FORMAT: Final = "%Y-%m-%d %H:%M:%S"
"""Splash datetime format."""


class Lists:
    """List fields: ``field@list`` identifiers (Php-Core ``ListsHelper``)."""

    @staticmethod
    def encode(list_name: str, field_name: str) -> str | None:
        """Build ``field@list``, None when a part is empty."""
        if not list_name or not field_name:
            return None
        return f"{field_name}{LIST_SPLIT}{list_name}"

    @staticmethod
    def explode(field_id: str | None) -> tuple[str, str] | None:
        """Split ``field@list`` into ``(field, list)``, None when not a list field."""
        if not field_id:
            return None
        parts = field_id.split(LIST_SPLIT)
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


class ObjectIds:
    """Object identifiers: ``id::Type`` (Php-Core ``ObjectsHelper``)."""

    @staticmethod
    def encode(object_type: str, object_id: str | int | None) -> str | None:
        """Build ``id::Type``, None when a part is empty."""
        if not object_type or object_id is None or object_id == "":
            return None
        return f"{object_id}{ID_SPLIT}{object_type}"

    @staticmethod
    def explode(value: str | None) -> tuple[str, str] | None:
        """Split ``id::Type`` into ``(id, Type)``, None when invalid."""
        if not value:
            return None
        parts = value.split(ID_SPLIT)
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


class Inline:
    """Inline fields: JSON arrays of strings (Php-Core ``InlineHelper``)."""

    @staticmethod
    def from_list(values: Iterable[Any]) -> str:
        """Encode values as an inline string."""
        items = list(values.values()) if isinstance(values, Mapping) else list(values)
        if not items:
            return "[]"
        # Same output as PHP json_encode(JSON_UNESCAPED_UNICODE): slashes are escaped
        return json.dumps(items, ensure_ascii=False, separators=(",", ":")).replace("/", "\\/")

    @staticmethod
    def to_list(value: str | None) -> list[Any]:
        """Decode an inline string, an empty list when invalid."""
        if not value or value in ("[]", "{}"):
            return []
        try:
            decoded = json.loads(value)
        except ValueError:
            return []
        if isinstance(decoded, dict):
            return list(decoded.values())
        return decoded if isinstance(decoded, list) else []


class Dates:
    """Splash dates and datetimes formats."""

    @staticmethod
    def to_date(value: date | None) -> str:
        """Format a date (empty string when None)."""
        return value.strftime(DATE_FORMAT) if value else ""

    @staticmethod
    def to_datetime(value: datetime | None) -> str:
        """Format a datetime (empty string when None)."""
        return value.strftime(DATETIME_FORMAT) if value else ""

    @staticmethod
    def parse_date(value: str | None) -> date | None:
        """Parse a Splash date, None when empty or invalid."""
        if not value:
            return None
        try:
            return datetime.strptime(value[:10], DATE_FORMAT).date()
        except ValueError:
            return None

    @staticmethod
    def parse_datetime(value: str | None) -> datetime | None:
        """Parse a Splash datetime (a date alone is accepted), None when empty or invalid."""
        if not value:
            return None
        for fmt in (DATETIME_FORMAT, DATE_FORMAT):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None
