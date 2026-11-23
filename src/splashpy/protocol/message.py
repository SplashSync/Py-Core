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

"""Pack and unpack Splash messages: XML encoding + encryption (Php-Core ``Webservice::pack()``)."""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
from typing import Any

from splashpy.dictionary import SplDefinition
from splashpy.protocol.cipher import LegacyCipher
from splashpy.protocol.codec import XmlCodec
from splashpy.protocol.errors import CipherError, MessageError


class MessageCodec:
    """Pack and unpack the ``data`` parameter of Splash SOAP calls."""

    # ====================================================================#
    # Constructor
    # ====================================================================#

    def __init__(self, key: str, ws_id: str) -> None:
        """Prepare the codec for one webservice id and encryption key."""
        self._cipher = LegacyCipher(key, ws_id)
        self._xml = XmlCodec()

    # ====================================================================#
    # Public API
    # ====================================================================#

    def pack(self, data: Mapping[str, Any], secured: bool = True) -> str:
        """Encode, then encrypt (or only base64 encode when not secured) a message.

        :raises MessageError: when the message cannot be encoded or encrypted.
        """
        xml = self._xml.encode(data)
        if not secured:
            return base64.b64encode(xml.encode("utf-8")).decode("ascii")
        try:
            return self._cipher.encrypt(xml)
        except CipherError as error:
            raise MessageError(str(error)) from error

    def unpack(self, raw: str, secured: bool = True) -> dict[str, Any]:
        """Decrypt (or only base64 decode when not secured), then decode a message.

        :raises MessageError: when the message cannot be decrypted or decoded.
        """
        try:
            xml = self._cipher.decrypt(raw) if raw and secured else base64.b64decode(raw, validate=True).decode("utf-8")
        except (CipherError, binascii.Error, ValueError) as error:
            raise MessageError(f"Unable to read message: {error}") from error
        if f"<{SplDefinition.XML_ROOT}>" not in xml:
            raise MessageError("Message is not a Splash message.")
        decoded = self._xml.decode(xml)
        if not decoded:
            raise MessageError("Message is empty.")

        return decoded
