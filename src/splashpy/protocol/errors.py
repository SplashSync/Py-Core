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

"""Exceptions raised by the wire protocol layer."""

from __future__ import annotations


class ProtocolError(Exception):
    """Base class of every wire protocol error."""


class XmlError(ProtocolError):
    """Raised when an XML document is invalid or refused for safety reasons."""


class CipherError(ProtocolError):
    """Raised when a message cannot be encrypted or decrypted."""


class MessageError(ProtocolError):
    """Raised when a Splash message cannot be packed or unpacked."""


class SoapError(ProtocolError):
    """Raised when a SOAP envelope is invalid."""


class SoapFault(ProtocolError):  # noqa: N818 - name of the SOAP concept
    """Raised when the remote side answered with a SOAP fault."""

    def __init__(self, code: str, message: str) -> None:
        """Store the fault code and message."""
        super().__init__(f"SOAP Fault [{code}] {message}")
        self.code = code
        self.message = message
