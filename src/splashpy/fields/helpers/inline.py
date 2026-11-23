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


"""Inline values (mirror of Php-Core ``InlineHelper``)."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any


class Inline:
    """Inline fields: JSON arrays of strings."""

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
