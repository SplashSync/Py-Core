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
It provides the faker objects (``short``, ``simple``, ``list``, ``primary``, ``image``,
``file``) stored in memory (SQLite), and two widgets. Values are returned exactly as
received, so the Splash Toolkit suites can check every field type.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from typing import Final

from splashpy.core.info import ClientInfo
from splashpy.extensions import Extension
from splashpy.faker.objects import OBJECTS
from splashpy.faker.objects.thirdparty import SCOPE
from splashpy.faker.store import FakerStore
from splashpy.faker.widgets import WIDGETS
from splashpy.objects import BaseObject
from splashpy.version import __version__
from splashpy.widgets import BaseWidget

FAKER_WS_ID: Final = "ThisIsSplashWsId"
"""Development webservice id of the faker (public, test only)."""

FAKER_WS_KEY: Final = "ThisIsYourEncryptionKeyForSplash"
"""Development encryption key of the faker (public, test only)."""


class FakerExtension(Extension):
    """Faker extension: turns a client into a demo node."""

    name = "faker"

    def __init__(self, store: FakerStore | None = None) -> None:
        """Use a store (a new in-memory one by default)."""
        self.store = store or FakerStore()

    def objects(self) -> Sequence[BaseObject]:
        """Faker objects."""
        return tuple(object_class(self.store) for object_class in OBJECTS)

    def widgets(self) -> Sequence[type[BaseWidget]]:
        """Faker widgets."""
        return WIDGETS

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
            scopes=[*info.scopes, SCOPE],
        )


__all__ = ["FAKER_WS_ID", "FAKER_WS_KEY", "FakerExtension"]
