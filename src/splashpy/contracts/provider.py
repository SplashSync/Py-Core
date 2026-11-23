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


"""Contracts provider: the catalog to use, without ever downloading anything.

Order: a valid cached catalog newer than the embedded one (updated by ``splashpy contracts update``),
otherwise the snapshot embedded in the package. An invalid cache is ignored with a warning, an older
or identical one silently: the embedded snapshot always works, offline included.
"""

from __future__ import annotations

import logging
import threading
from functools import lru_cache
from importlib import resources

from splashpy.contracts.cache import CatalogCache, FileCache
from splashpy.contracts.catalog import Catalog, ContractsError
from splashpy.dictionary import SplContracts

_LOGGER = logging.getLogger("splashpy.contracts")
"""Contracts logger."""

EMBEDDED = "embedded"
"""Origin of the embedded snapshot."""


class ContractsProvider:
    """Load the catalog once: cache when valid and newer, embedded snapshot otherwise."""

    def __init__(self, cache: CatalogCache | None = None) -> None:
        """Use a cache (None: embedded snapshot only)."""
        self.cache = cache
        self._catalog: Catalog | None = None
        self._mutex = threading.Lock()

    def catalog(self) -> Catalog:
        """Get the catalog (loaded on first use)."""
        with self._mutex:
            if self._catalog is None:
                self._catalog = self._load()
            return self._catalog

    def _load(self) -> Catalog:
        """Load the cached catalog when valid and newer than the embedded one, or the embedded one."""
        embedded = embedded_catalog()
        if self.cache is None or self.cache.read(SplContracts.INDEX) is None:
            return embedded
        try:
            cached = Catalog.load(self.cache.read, "cache")
        except ContractsError as error:
            _LOGGER.warning("Cached contracts catalog ignored, embedded one used: %s", error)
            return embedded
        return cached if cached.is_newer_than(embedded) else embedded


@lru_cache(maxsize=1)
def embedded_catalog() -> Catalog:
    """Get the catalog embedded in the package (always available)."""
    return Catalog.load(_read_embedded, EMBEDDED)


@lru_cache(maxsize=1)
def default_provider() -> ContractsProvider:
    """Get the provider used when none is given: user file cache, then embedded snapshot."""
    return ContractsProvider(FileCache())


def default_catalog() -> Catalog:
    """Get the catalog used when none is given."""
    return default_provider().catalog()


def _read_embedded(name: str) -> bytes | None:
    """Read a file of the embedded snapshot."""
    try:
        return resources.files("splashpy.contracts").joinpath("data").joinpath(name).read_bytes()
    except OSError:
        return None
