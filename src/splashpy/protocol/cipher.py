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

"""Legacy Splash message encryption (AES-256-CBC), byte compatible with Php-Core.

Php-Core computes ``openssl_encrypt($data, 'AES-256-CBC', hash('sha256', $key), 0, $iv)``
then base64 encodes the (already base64) result:

- key: the first 32 characters of the hexadecimal SHA-256 of the encryption key;
- IV: the first 16 characters of the hexadecimal SHA-256 of the webservice id;
- PKCS#7 padding, double base64 encoding.

This scheme has known weaknesses (static IV, no authentication). It is kept strictly
identical for wire compatibility: changing it is a protocol level decision.
"""

from __future__ import annotations

import base64
import binascii
import hashlib

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from splashpy.protocol.errors import CipherError

_BLOCK_BITS = 128
"""AES block size, in bits."""


class LegacyCipher:
    """Encrypt and decrypt Splash messages with the shared encryption key."""

    # ====================================================================#
    # Constructor
    # ====================================================================#

    def __init__(self, key: str, ws_id: str) -> None:
        """Derive the AES key and IV from the encryption key and the webservice id.

        :raises CipherError: when the key or the id is empty.
        """
        if not key or not ws_id:
            raise CipherError("Encryption key and webservice id are required.")
        self._key = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32].encode("ascii")
        self._iv = hashlib.sha256(ws_id.encode("utf-8")).hexdigest()[:16].encode("ascii")

    # ====================================================================#
    # Public API
    # ====================================================================#

    def encrypt(self, plain: str) -> str:
        """Encrypt a message.

        :raises CipherError: when the message is empty.
        """
        if not plain:
            raise CipherError("Unable to encrypt an empty message.")
        padder = padding.PKCS7(_BLOCK_BITS).padder()
        padded = padder.update(plain.encode("utf-8")) + padder.finalize()
        encryptor = self._cipher().encryptor()
        encrypted = encryptor.update(padded) + encryptor.finalize()

        return base64.b64encode(base64.b64encode(encrypted)).decode("ascii")

    def decrypt(self, data: str) -> str:
        """Decrypt a message.

        :raises CipherError: when the message is empty, badly encoded or badly padded.
        """
        if not data:
            raise CipherError("Unable to decrypt an empty message.")
        try:
            encrypted = base64.b64decode(base64.b64decode(data.strip(), validate=True))
        except (binascii.Error, ValueError) as error:
            raise CipherError(f"Invalid encrypted message encoding: {error}") from error
        if not encrypted or len(encrypted) % (_BLOCK_BITS // 8):
            raise CipherError("Invalid encrypted message length.")
        decryptor = self._cipher().decryptor()
        padded = decryptor.update(encrypted) + decryptor.finalize()
        unpadder = padding.PKCS7(_BLOCK_BITS).unpadder()
        try:
            plain = unpadder.update(padded) + unpadder.finalize()
            return plain.decode("utf-8")
        except ValueError as error:
            raise CipherError("Unable to decrypt message: wrong key or corrupted data.") from error

    # ====================================================================#
    # Private Methods
    # ====================================================================#

    def _cipher(self) -> Cipher[modes.CBC]:
        """Build the AES-256-CBC cipher."""
        # Legacy protocol encryption, kept identical for compatibility.
        return Cipher(algorithms.AES(self._key), modes.CBC(self._iv))  # nosec B305
