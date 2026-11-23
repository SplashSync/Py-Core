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

"""Splash XML codec, byte compatible with Php-Core ``XmlManager``.

Encoding rules:

- the root element is ``<SPLASH>``, indented with one space per level;
- every scalar is written base64 encoded: strings as is, booleans as ``1`` / ``0``,
  numbers with the PHP string conversion (``precision = 14``), ``None`` as empty;
- mappings and sequences become nested elements; an empty one is ``<key/>``;
- numeric keys (list indexes included) are prefixed by the value kind:
  ``array-``, ``string-``, ``int-`` or ``bool-``;
- any character outside ``[a-zA-Z0-9-]`` in a key is replaced by ``_``.

Decoding returns what PHP ``xmlToArray`` returns: values are always strings,
nested elements become dicts, repeated element names become lists.
"""

from __future__ import annotations

import base64
import binascii
import math
import re
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any, Final, Union

from splashpy.dictionary import SplDefinition
from splashpy.protocol import xmlsafe
from splashpy.protocol.errors import MessageError

# ====================================================================#
# Types
# ====================================================================#

DecodedValue = Union[str, dict[str, Any], list[Any]]
"""A decoded value: always a string, a dict or a list (PHP arrays semantics)."""

# ====================================================================#
# Constants
# ====================================================================#

PREFIX_ARRAY: Final = "array-"
"""Prefix of numeric keys holding an array."""

PREFIX_STRING: Final = "string-"
"""Prefix of numeric keys holding a string."""

PREFIX_NUMBER: Final = "int-"
"""Prefix of numeric keys holding a number (integer or float)."""

PREFIX_BOOL: Final = "bool-"
"""Prefix of numeric keys holding a boolean."""

_PHP_NUMERIC: Final = re.compile(r"^[ \t\n\r\v\f]*[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?[ \t\n\r\v\f]*$")
"""PHP ``is_numeric()`` for strings."""

_INVALID_KEY_CHARS: Final = re.compile(r"[^a-zA-Z0-9\-]")
"""Characters replaced by ``_`` in element names."""

_PHP_PRECISION: Final = 14
"""PHP ``precision`` ini setting, used by the float to string conversion."""


class XmlCodec:
    """Encode and decode Splash messages contents."""

    # ====================================================================#
    # Public API
    # ====================================================================#

    def encode(self, data: Mapping[Any, Any], declaration: bool = False) -> str:
        """Encode a mapping into a Splash XML document.

        :param data: message contents.
        :param declaration: prepend the ``<?xml version="1.0"?>`` declaration.
        """
        lines: list[str] = ['<?xml version="1.0"?>'] if declaration else []
        root = SplDefinition.XML_ROOT
        if not data:
            lines.append(f"<{root}/>")
        else:
            lines.append(f"<{root}>")
            for key, value in data.items():
                self._write(lines, key, value, 1)
            lines.append(f"</{root}>")

        return "\n".join(lines) + "\n"

    def decode(self, document: str) -> dict[str, Any] | None:
        """Decode a Splash XML document.

        :return: decoded contents, or None when the document has no ``<SPLASH>`` contents.
        :raises MessageError: when the document is not valid XML.
        """
        try:
            root = xmlsafe.parse(document)
        except Exception as error:
            raise MessageError(f"Unable to decode Splash XML: {error}") from error
        if root.tag != SplDefinition.XML_ROOT:
            return None
        result = self._read(root)

        return result if isinstance(result, dict) else None

    # ====================================================================#
    # Static Helpers
    # ====================================================================#

    @staticmethod
    def php_number(value: int | float | Decimal) -> str:
        """Convert a number to a string exactly like PHP ``(string) $number``."""
        if isinstance(value, int):
            return str(value)
        if isinstance(value, Decimal):
            return str(value)
        if math.isnan(value):
            return "NAN"
        if math.isinf(value):
            return "INF" if value > 0 else "-INF"
        formatted = format(value, f".{_PHP_PRECISION}G")
        if "E" not in formatted:
            return formatted
        mantissa, exponent = formatted.split("E")
        if "." not in mantissa:
            mantissa += ".0"
        exp = int(exponent)

        return f"{mantissa}E{'+' if exp >= 0 else '-'}{abs(exp)}"

    @staticmethod
    def is_php_numeric(key: Any) -> bool:
        """Mirror of PHP ``is_numeric()`` applied to an array key."""
        if isinstance(key, bool):
            return False
        if isinstance(key, (int, float, Decimal)):
            return True

        return bool(_PHP_NUMERIC.match(str(key)))

    @staticmethod
    def element_name(key: Any, prefix: str) -> str:
        """Build an element name from a key, as Php-Core ``keysFilter()``."""
        name = str(key)
        if XmlCodec.is_php_numeric(key):
            name = prefix + name

        return _INVALID_KEY_CHARS.sub("_", name)

    # ====================================================================#
    # Private Methods
    # ====================================================================#

    def _write(self, lines: list[str], key: Any, value: Any, depth: int) -> None:
        """Append the element(s) of one key / value pair."""
        indent = " " * depth
        # ====================================================================#
        # Arrays: Mappings & Sequences (but not strings)
        if isinstance(value, Mapping) or (
            isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
        ):
            name = self.element_name(key, PREFIX_ARRAY)
            items = value.items() if isinstance(value, Mapping) else enumerate(value)
            if not value:
                lines.append(f"{indent}<{name}/>")
                return
            lines.append(f"{indent}<{name}>")
            for child_key, child_value in items:
                self._write(lines, child_key, child_value, depth + 1)
            lines.append(f"{indent}</{name}>")
            return
        # ====================================================================#
        # Scalars
        prefix, raw = self._scalar(value)
        name = self.element_name(key, prefix)
        text = base64.b64encode(raw).decode("ascii")
        lines.append(f"{indent}<{name}>{text}</{name}>")

    def _scalar(self, value: Any) -> tuple[str, bytes]:
        """Get the numeric-key prefix and the raw bytes of a scalar value."""
        if value is None:
            # PHP crashes on a null value with a numeric key: we write an empty string instead.
            return PREFIX_STRING, b""
        if isinstance(value, (bytes, bytearray)):
            return PREFIX_STRING, bytes(value)
        if isinstance(value, str):
            return PREFIX_STRING, value.encode("utf-8")
        if isinstance(value, bool):
            return PREFIX_BOOL, b"1" if value else b"0"
        if isinstance(value, (int, float, Decimal)):
            return PREFIX_NUMBER, self.php_number(value).encode("ascii")
        raise MessageError(f"Unable to encode value of type {type(value).__name__}.")

    def _read(self, element: xmlsafe.Element) -> DecodedValue:
        """Recursively decode an element, as Php-Core ``simpleXmlToArray()``."""
        children = list(element)
        if not children:
            return self._b64_text(element.text)
        result: dict[str, Any] = {}
        for child in children:
            name = child.tag
            value = self._read(child)
            if name not in result:
                result[name] = value
                continue
            current = result[name]
            if isinstance(current, list):
                current.append(value)
            elif isinstance(current, dict):
                # PHP appends to the existing array with the next integer key
                int_keys = [int(k) for k in current if isinstance(k, int) or str(k).isdigit()]
                current[str(max(int_keys) + 1 if int_keys else 0)] = value
            else:
                result[name] = [current, value]

        return result

    @staticmethod
    def _b64_text(text: str | None) -> str:
        """Decode a base64 text node, as PHP ``base64_decode($text, true)`` cast to string."""
        if not text:
            return ""
        try:
            raw = base64.b64decode("".join(text.split()), validate=True)
        except (binascii.Error, ValueError):
            return ""

        return raw.decode("utf-8", errors="surrogateescape")
