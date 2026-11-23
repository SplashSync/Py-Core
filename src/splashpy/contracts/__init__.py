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


"""Contracts: Splash field templates and scopes, from the Php-Scopes catalog.

The package embeds a catalog snapshot: templates and scopes always work, offline included.
``splashpy contracts update`` may download a newer catalog into a local cache, used when valid.
"""

from __future__ import annotations

from splashpy.contracts.cache import CatalogCache, FileCache
from splashpy.contracts.catalog import Catalog, ContractsError
from splashpy.contracts.provider import ContractsProvider, default_catalog, embedded_catalog
from splashpy.contracts.updater import UpdateResult, catalog_url, update

__all__ = [
    "Catalog",
    "CatalogCache",
    "ContractsError",
    "ContractsProvider",
    "FileCache",
    "UpdateResult",
    "catalog_url",
    "default_catalog",
    "embedded_catalog",
    "update",
]
