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

"""Faker: a demo connector for development and tests ONLY.

It ships inside the package but is NEVER enabled implicitly: it must be enabled
explicitly (``splashpy serve --faker`` or by registering :class:`FakerExtension`).
Milestone 1 only provides client information; objects and widgets come later.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Final

from splashpy.core.info import ClientInfo
from splashpy.extensions import Extension
from splashpy.version import __version__

FAKER_WS_ID: Final = "ThisIsSplashWsId"
"""Development webservice id of the faker (public, test only)."""

FAKER_WS_KEY: Final = "ThisIsYourEncryptionKeyForSplash"
"""Development encryption key of the faker (public, test only)."""


class FakerExtension(Extension):
    """Faker extension: turns a client into a demo node."""

    name = "faker"

    def client_info(self, info: ClientInfo) -> ClientInfo:
        """Present the client as the splashpy faker."""
        return replace(
            info,
            shortdesc=f"Splash Python Faker {__version__}",
            longdesc="Demo connector of splashpy, for development and tests only.",
            company="Splash Sync",
            address="Python Street",
            zip="00000",
            town="Faker Town",
            country="France",
            www="https://www.splashsync.com",
            email="contact@splashsync.com",
            phone="+33 0 00 00 00 00",
            servertype="Splash Python Faker",
            serverurl="https://www.splashsync.com",
        )


__all__ = ["FAKER_WS_ID", "FAKER_WS_KEY", "FakerExtension"]
