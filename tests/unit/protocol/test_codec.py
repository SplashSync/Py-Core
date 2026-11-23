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

"""XML codec behaviours not covered by golden fixtures."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from splashpy.protocol import MessageError, XmlCodec


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (100.0, "100"),
        (12.5, "12.5"),
        (0.1 + 0.2, "0.3"),
        (1e-5, "1.0E-5"),
        (1.5e-7, "1.5E-7"),
        (1e20, "1.0E+20"),
        (1e15, "1.0E+15"),
        (123456789012345.678, "1.2345678901235E+14"),
        (-0.75, "-0.75"),
        (float("nan"), "NAN"),
        (float("inf"), "INF"),
        (float("-inf"), "-INF"),
        (7, "7"),
        (Decimal("12.30"), "12.30"),
    ],
)
def test_php_number(value: Any, expected: str) -> None:
    """Numbers are converted like PHP ``(string) $number`` with ``precision = 14``."""
    assert XmlCodec.php_number(value) == expected


@pytest.mark.parametrize(
    ("key", "expected"),
    [(0, True), ("12", True), (" 12", True), ("1.5", True), ("1e3", True), ("012", True), ("abc", False)],
)
def test_is_php_numeric(key: Any, expected: bool) -> None:
    """Keys numeric for PHP get a type prefix."""
    assert XmlCodec.is_php_numeric(key) is expected


def test_bool_key_is_not_numeric() -> None:
    """A boolean key is not numeric."""
    assert XmlCodec.is_php_numeric(True) is False


def test_encode_empty_message() -> None:
    """An empty message is an empty root element."""
    assert XmlCodec().encode({}) == "<SPLASH/>\n"


def test_encode_null_list_item_does_not_crash() -> None:
    """PHP crashes on null list items: Python writes an empty string instead."""
    xml = XmlCodec().encode({"list": [None, "a"]})
    assert "<string-0></string-0>" in xml
    assert XmlCodec().decode(xml) == {"list": {"string-0": "", "string-1": "a"}}


def test_encode_bytes_and_tuples() -> None:
    """Bytes are written as is, tuples as lists."""
    codec = XmlCodec()
    decoded = codec.decode(codec.encode({"raw": b"\x00\x01binary", "tuple": ("x", 1)}))
    assert decoded == {"raw": "\x00\x01binary", "tuple": {"string-0": "x", "int-1": "1"}}


def test_encode_unsupported_type() -> None:
    """Unsupported values are refused explicitly."""
    with pytest.raises(MessageError):
        XmlCodec().encode({"object": object()})


def test_decode_repeated_elements() -> None:
    """Repeated element names become lists, as PHP does."""
    xml = "<SPLASH><a>MQ==</a><a>Mg==</a><a>Mw==</a></SPLASH>"
    assert XmlCodec().decode(xml) == {"a": ["1", "2", "3"]}


def test_decode_repeated_array_elements() -> None:
    """A repeated element whose first value is an array is appended to it, as PHP does."""
    xml = "<SPLASH><a><b>MQ==</b></a><a><c>Mg==</c></a></SPLASH>"
    assert XmlCodec().decode(xml) == {"a": {"b": "1", "0": {"c": "2"}}}


def test_decode_invalid_base64_is_empty() -> None:
    """Invalid base64 decodes to an empty string, as PHP strict decoding cast to string."""
    assert XmlCodec().decode("<SPLASH><a>!!!</a></SPLASH>") == {"a": ""}


def test_decode_other_root_is_none() -> None:
    """Documents without SPLASH root are not Splash messages."""
    assert XmlCodec().decode("<OTHER><a>MQ==</a></OTHER>") is None
    assert XmlCodec().decode("<SPLASH>MQ==</SPLASH>") is None


def test_decode_malformed() -> None:
    """Malformed XML is reported."""
    with pytest.raises(MessageError):
        XmlCodec().decode("<SPLASH><a></SPLASH>")
