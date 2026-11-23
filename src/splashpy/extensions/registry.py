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

"""Per-client extensions registry.

Two ways in, nothing implicit:

- explicit registration (hosts whose add-ons are not pip packages, e.g. Odoo);
- installed packages declaring an entry point in the ``splash`` group, enabled only
  when their name is listed in the client configuration (``extensions``).
"""

from __future__ import annotations

import sys
from collections.abc import Iterable
from importlib import metadata
from typing import Final

from splashpy.config import ConfigError
from splashpy.extensions import Extension

ENTRY_POINTS_GROUP: Final = "splash"
"""Entry points group of splashpy extensions."""


def installed() -> dict[str, metadata.EntryPoint]:
    """List installed extensions (entry points), by name. Nothing is loaded."""
    if sys.version_info >= (3, 10):
        points = metadata.entry_points(group=ENTRY_POINTS_GROUP)
    else:  # pragma: no cover - Python 3.9 API
        points = metadata.entry_points().get(ENTRY_POINTS_GROUP, ())
    return {point.name: point for point in points}


class ExtensionsRegistry:
    """Extensions enabled for one client."""

    def __init__(self, extensions: Iterable[Extension] = (), enabled: Iterable[str] = ()) -> None:
        """Register explicit extensions, then load installed ones listed in ``enabled``.

        :raises ConfigError: when an enabled name is not installed or is not an extension.
        """
        self._extensions: dict[str, Extension] = {}
        for extension in extensions:
            self.register(extension)
        if enabled:
            self.load(enabled)

    def register(self, extension: Extension) -> ExtensionsRegistry:
        """Enable an extension instance.

        :raises ConfigError: when another extension already uses the same name.
        """
        name = extension.name or type(extension).__name__
        current = self._extensions.get(name)
        if current is not None and current is not extension:
            raise ConfigError(f"Extension name '{name}' is used twice.")
        self._extensions[name] = extension
        return self

    def load(self, names: Iterable[str]) -> ExtensionsRegistry:
        """Enable installed extensions by name.

        :raises ConfigError: when a name is not installed or is not an extension.
        """
        available = installed()
        for name in names:
            if name in self._extensions:
                continue
            point = available.get(name)
            if point is None:
                raise ConfigError(f"Extension '{name}' is not installed.")
            loaded = point.load()
            extension = loaded() if isinstance(loaded, type) else loaded
            if not isinstance(extension, Extension):
                raise ConfigError(f"Entry point '{name}' is not a splashpy extension.")
            self.register(extension)
        return self

    def all(self) -> tuple[Extension, ...]:
        """Get enabled extensions, by priority then name."""
        return tuple(sorted(self._extensions.values(), key=lambda ext: (ext.priority, ext.name)))

    def names(self) -> list[str]:
        """Names of enabled extensions."""
        return [extension.name or type(extension).__name__ for extension in self.all()]
