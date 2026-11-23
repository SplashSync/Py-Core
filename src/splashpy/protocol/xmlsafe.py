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

"""Safe XML parsing.

SOAP envelopes are parsed BEFORE any authentication, so untrusted input must never
be able to trigger entity expansion ("billion laughs") or external entity loading.
Splash messages never use a DTD: any document declaring one is refused before
being handed to the parser. Without a DTD, no entity can be declared at all.
"""

from __future__ import annotations

import re

# Parsing is only done through parse() below, which refuses any DTD.
import xml.etree.ElementTree as ET  # nosec B405
from typing import Final

from splashpy.protocol.errors import XmlError

MAX_SIZE: Final = 128 * 1024 * 1024
"""Default maximum accepted document size, in bytes (files travel inside messages)."""

Element = ET.Element
"""Parsed XML element type."""

_FORBIDDEN: Final = re.compile(rb"<!\s*(DOCTYPE|ENTITY)", re.IGNORECASE)
"""Markup declarations that are never accepted."""


def parse(document: bytes | str, max_size: int = MAX_SIZE) -> Element:
    """Parse an XML document safely and return its root element.

    :raises XmlError: when the document is too large, declares a DTD or is malformed.
    """
    raw = document.encode("utf-8") if isinstance(document, str) else document
    if len(raw) > max_size:
        raise XmlError(f"XML document too large ({len(raw)} bytes, max {max_size}).")
    if _FORBIDDEN.search(raw):
        raise XmlError("XML document declares a DTD or an entity: refused.")
    try:
        # Safe: any DTD was refused above, so no entity can be declared.
        return ET.fromstring(raw)  # nosec B314
    except ET.ParseError as error:
        raise XmlError(f"Malformed XML document: {error}") from error
