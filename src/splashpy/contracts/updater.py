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


"""Contracts updater: download the latest catalog into a cache (never on a request path).

The index is downloaded first: when its commit is the one of the catalog in use (cache or embedded
snapshot), nothing else is downloaded, nothing is written. Otherwise each file is downloaded,
checked against the index (SHA-256), the whole catalog is checked (supported format), and only
then written to the cache, index last.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Callable

from splashpy.contracts.cache import CatalogCache
from splashpy.contracts.catalog import Catalog, ContractsError
from splashpy.contracts.provider import ContractsProvider
from splashpy.dictionary import SplContracts
from splashpy.version import __version__

Fetcher = Callable[[str], bytes]
"""Downloads a URL, raises ``OSError`` on failure."""


@dataclass(frozen=True)
class UpdateResult:
    """Result of an update."""

    updated: bool
    """True when new files were written to the cache."""

    version: str
    """Version of the cached catalog."""

    commit: str
    """Commit of the cached catalog."""


def catalog_url(name: str, version: str = SplContracts.VERSION) -> str:
    """URL of a catalog file in the registry."""
    return f"{SplContracts.REGISTRY}/{version}/{name}"


def http_fetch(url: str) -> bytes:
    """Download a URL with the standard library."""
    request = urllib.request.Request(url, headers={"User-Agent": f"splashpy/{__version__}"})
    with urllib.request.urlopen(request, timeout=SplContracts.TIMEOUT) as response:  # nosec B310 - fixed https registry
        return bytes(response.read())


def update(cache: CatalogCache, version: str = SplContracts.VERSION, fetch: Fetcher | None = None) -> UpdateResult:
    """Download a catalog version into a cache, only when it differs from the catalog in use.

    The index is downloaded first. When its commit is the one of the catalog in use (the cache when
    valid and newer, the embedded snapshot otherwise), nothing else is downloaded nor written.

    :param fetch: downloader (``http_fetch`` by default).
    :raises ContractsError: when the download fails or the catalog is invalid (the cache is unchanged).
    """
    fetch = fetch or http_fetch
    downloaded = {SplContracts.INDEX: _fetch(fetch, catalog_url(SplContracts.INDEX, version))}
    current = ContractsProvider(cache).catalog()
    if _commit(downloaded[SplContracts.INDEX]) == current.commit:
        return UpdateResult(False, current.version, current.commit)
    for name in SplContracts.FILES:
        downloaded[name] = _fetch(fetch, catalog_url(name, version))
    catalog = Catalog.load(downloaded.get, catalog_url("", version))
    for name in (*SplContracts.FILES, SplContracts.INDEX):
        cache.write(name, downloaded[name])
    return UpdateResult(True, catalog.version, catalog.commit)


def _fetch(fetch: Fetcher, url: str) -> bytes:
    """Download a file, network errors as contracts errors."""
    try:
        return fetch(url)
    except OSError as error:
        raise ContractsError(f"Unable to download {url}: {error}") from error


def _commit(raw: bytes) -> str | None:
    """Commit of an index, None when unreadable."""
    try:
        index = json.loads(raw)
    except ValueError:
        return None
    return str(index.get("commit")) if isinstance(index, dict) else None
