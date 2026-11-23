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

"""Cipher and message codec error handling."""

from __future__ import annotations

import base64

import pytest

from splashpy.protocol import CipherError, LegacyCipher, MessageCodec, MessageError


def test_cipher_requires_credentials() -> None:
    """Key and id are mandatory."""
    with pytest.raises(CipherError):
        LegacyCipher("", "id")
    with pytest.raises(CipherError):
        LegacyCipher("key", "")


def test_cipher_refuses_empty_messages() -> None:
    """Empty messages are refused both ways."""
    cipher = LegacyCipher("key", "id")
    with pytest.raises(CipherError):
        cipher.encrypt("")
    with pytest.raises(CipherError):
        cipher.decrypt("")


def test_cipher_wrong_key() -> None:
    """A message encrypted with another key is refused (bad padding)."""
    encrypted = LegacyCipher("key", "id").encrypt("<SPLASH>secret</SPLASH>")
    try:
        result = LegacyCipher("other", "id").decrypt(encrypted)
    except CipherError:
        return
    # A wrong key may exceptionally produce a valid padding: never the plain text
    assert result != "<SPLASH>secret</SPLASH>"


@pytest.mark.parametrize(
    "data",
    ["not base64 !", base64.b64encode(b"not base64 !").decode(), base64.b64encode(base64.b64encode(b"short")).decode()],
)
def test_cipher_invalid_encoding(data: str) -> None:
    """Badly encoded messages are refused."""
    with pytest.raises(CipherError):
        LegacyCipher("key", "id").decrypt(data)


def test_message_roundtrip() -> None:
    """Pack then unpack gives decoded (string) values."""
    codec = MessageCodec("key", "id")
    packed = codec.pack({"result": True, "count": 3, "list": ["a"]})
    assert codec.unpack(packed) == {"result": "1", "count": "3", "list": {"string-0": "a"}}


@pytest.mark.parametrize(
    ("raw", "secured"),
    [
        ("", True),
        ("garbage", True),
        (base64.b64encode(b"<OTHER/>").decode(), False),
        (base64.b64encode(b"<SPLASH></SPLASH>").decode(), False),
        ("%%%", False),
    ],
)
def test_message_unpack_errors(raw: str, secured: bool) -> None:
    """Unreadable, foreign or empty messages are refused."""
    with pytest.raises(MessageError):
        MessageCodec("key", "id").unpack(raw, secured)
