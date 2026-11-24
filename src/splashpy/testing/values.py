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


"""Conformance values: generate field values, send them like Splash, compare what comes back.

Values travel through the real wire codec in both directions (``wire()``): a connector receives
strings, exactly as from Splash, and what it returns is compared after encoding, with a
comparator per field type (numbers, booleans, prices, dates, inline lists...).
"""

from __future__ import annotations

import random
import string
from collections.abc import Mapping
from datetime import date, datetime, timedelta
from typing import Any, Callable, Final

from splashpy.fields import Dates, Inline, Lists, Prices
from splashpy.fields.types import FieldType
from splashpy.protocol import XmlCodec

SKIPPED_TYPES: Final = (FieldType.FILE, FieldType.IMAGE, FieldType.STREAM, FieldType.OBJECT_ID)
"""Types never generated: files need Splash, object links need another object."""

_WIRE_KEY: Final = "value"
"""Key used to send a single value through the codec."""


def wire(value: Any) -> Any:
    """Send a value through the Splash wire codec (encode, then decode), like Splash would."""
    codec = XmlCodec()
    decoded = codec.decode(codec.encode({_WIRE_KEY: value}))
    return decoded.get(_WIRE_KEY) if decoded else None


def base_type(field: Mapping[str, Any]) -> str:
    """Type of the values of a field definition (inner type of lists, ``objectid`` for links)."""
    field_type = Lists.field_name(str(field["type"])) or str(field["type"])
    return FieldType.OBJECT_ID if field_type.startswith(f"{FieldType.OBJECT_ID}::") else field_type


def is_testable(field: Mapping[str, Any]) -> bool:
    """Check if a field can be written then read back by the conformance suite."""
    return bool(field.get("read") and field.get("write") and not field.get("notest")) and (
        base_type(field) not in SKIPPED_TYPES
    )


class ValuesGenerator:
    """Generate valid field values, reproducible from a seed."""

    def __init__(self, seed: int = 0) -> None:
        """Start a reproducible sequence."""
        self._random = random.Random(seed)  # nosec B311 - test data, not security

    def value(self, field: Mapping[str, Any]) -> Any:
        """Generate a value for a field definition (choices first, then by type)."""
        choices = [choice["key"] for choice in field.get("choices") or [] if choice.get("key")]
        if choices:
            return self._random.choice(choices)
        generate: Callable[[Mapping[str, Any]], Any] = self._generators().get(base_type(field), self._text)
        value = generate(field)
        max_length = (field.get("options") or {}).get("maxLength")
        if isinstance(value, str) and isinstance(max_length, int) and max_length > 0:
            value = value[:max_length]
        return value

    def values(self, fields: Mapping[str, Mapping[str, Any]], items: int = 2) -> dict[str, Any]:
        """Generate values for every testable field: plain fields by id, list fields by list name."""
        values: dict[str, Any] = {}
        lists: dict[str, list[dict[str, Any]]] = {}
        for field_id, field in fields.items():
            if not is_testable(field):
                continue
            parts = Lists.explode(field_id)
            if parts is None:
                values[field_id] = self.value(field)
                continue
            rows = lists.setdefault(parts[1], [{} for _ in range(items)])
            for row in rows:
                row[parts[0]] = self.value(field)
        return {**values, **lists}

    def _generators(self) -> dict[str, Callable[[Mapping[str, Any]], Any]]:
        """Get the generators, by base type."""
        return {
            FieldType.BOOL: lambda field: self._random.choice((True, False)),
            FieldType.INT: lambda field: self._random.randint(1, 10000),
            FieldType.DOUBLE: lambda field: round(self._random.uniform(1, 1000), 2),
            FieldType.EMAIL: lambda field: f"{self._word(8)}@example.com",
            FieldType.PHONE: lambda field: f"+33 1 {self._random.randint(10, 99)} 45 67 89",
            FieldType.URL: lambda field: f"https://www.example.com/{self._word(6)}",
            FieldType.DATE: lambda field: Dates.to_date(self._date()),
            FieldType.DATETIME: lambda field: Dates.to_datetime(datetime.combine(self._date(), datetime.min.time())),
            FieldType.LANG: lambda field: self._random.choice(("en_US", "fr_FR", "es_ES")),
            FieldType.COUNTRY: lambda field: self._random.choice(("FR", "US", "DE")),
            FieldType.STATE: lambda field: self._random.choice(("CA", "NY", "FL")),
            FieldType.CURRENCY: lambda field: self._random.choice(("EUR", "USD")),
            FieldType.PRICE: lambda field: Prices.encode(round(self._random.uniform(1, 1000), 2), 20.0, code="EUR"),
            FieldType.INLINE: lambda field: Inline.from_list([self._word(5) for _ in range(3)]),
        }

    def _text(self, field: Mapping[str, Any]) -> str:
        """Generate a text."""
        return f"{self._word(6)} {self._word(8)}"

    def _word(self, length: int) -> str:
        """Generate a lower case word."""
        return "".join(self._random.choice(string.ascii_lowercase) for _ in range(length))

    def _date(self) -> date:
        """Generate a date in the last years."""
        return date(2020, 1, 1) + timedelta(days=self._random.randint(0, 2000))


def same_value(field: Mapping[str, Any], sent: Any, received: Any) -> bool:
    """Compare a value sent to a connector with the value it gives back (both after ``wire()``)."""
    if _empty(sent) or _empty(received):
        return _empty(sent) and _empty(received)
    compare = _COMPARATORS.get(base_type(field))
    if compare is not None:
        return compare(sent, received)
    return str(sent) == str(received)


# ====================================================================#
# Comparators
# ====================================================================#


def _empty(value: Any) -> bool:
    """Empty value on the wire."""
    return value is None or value == "" or value == {}


def _numbers(precision: float) -> Callable[[Any, Any], bool]:
    """Compare numbers with a precision."""

    def compare(sent: Any, received: Any) -> bool:
        try:
            return abs(float(sent) - float(received)) <= precision
        except (TypeError, ValueError):
            return False

    return compare


def _booleans(sent: Any, received: Any) -> bool:
    """Compare booleans (PHP truthiness)."""
    return (sent not in ("", "0", 0, False)) == (received not in ("", "0", 0, False))


def _prices(sent: Any, received: Any) -> bool:
    """Compare prices."""
    return Prices.compare(sent, received)


def _dates(sent: Any, received: Any) -> bool:
    """Compare dates (the date part only)."""
    return Dates.parse_date(str(sent)) == Dates.parse_date(str(received))


def _datetimes(sent: Any, received: Any) -> bool:
    """Compare datetimes."""
    return Dates.parse_datetime(str(sent)) == Dates.parse_datetime(str(received))


def _inlines(sent: Any, received: Any) -> bool:
    """Compare inline lists, whatever the order."""
    return sorted(map(str, Inline.to_list(str(sent)))) == sorted(map(str, Inline.to_list(str(received))))


_COMPARATORS: Final = {
    FieldType.BOOL: _booleans,
    FieldType.INT: _numbers(0),
    FieldType.DOUBLE: _numbers(1e-6),
    FieldType.PRICE: _prices,
    FieldType.DATE: _dates,
    FieldType.DATETIME: _datetimes,
    FieldType.INLINE: _inlines,
}
"""Comparators by base type (others: text equality)."""
