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

"""General definitions of the Splash protocol and of this module."""

from __future__ import annotations

from typing import Final

from splashpy.version import __version__


class SplDefinition:
    """General Splash definitions (mirror of Php-Core ``SplDefinition``)."""

    # ====================================================================#
    # Module Identity
    # ====================================================================#

    NAME: Final = "Splash Python Core"
    """Module name, as shown to the Splash server."""

    DESC: Final = "Splash Open-Source & Universal Synchronisation WebService."
    """Module long description."""

    AUTHOR: Final = "Splash Official <www.splashsync.com>"
    """Module author."""

    VERSION: Final = __version__
    """Module version."""

    # ====================================================================#
    # Protocol
    # ====================================================================#

    PROTOCOL: Final = "1.2"
    """Splash protocol version, aligned on Php-Core 3.0."""

    SERVER_TYPE: Final = "Python"
    """Server language type, reported in server information."""

    WS_METHOD: Final = "SOAP"
    """Webservice method, reported in server information."""

    HOST: Final = "https://www.splashsync.com/ws/soap"
    """Default Splash server endpoint."""

    TIMEOUT: Final = 30
    """Default webservice timeout, in seconds."""

    CRYPT_METHOD: Final = "AES-256-CBC"
    """The only supported encryption method."""

    ENCODE: Final = "XML"
    """The only supported encoding."""

    LANG: Final = "en_US"
    """Default language."""

    XML_ROOT: Final = "SPLASH"
    """Root element of every Splash message."""
