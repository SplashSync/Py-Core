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


"""Contracts cache: where updated catalogs are kept (optional, the package embeds its own)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

from splashpy.dictionary import SplContracts


class CatalogCache(Protocol):
    """Storage of catalog files: any host storage can be plugged."""

    def read(self, name: str) -> bytes | None:
        """Read a catalog file, None when missing."""
        ...

    def write(self, name: str, raw: bytes) -> None:
        """Write a catalog file."""
        ...


class FileCache:
    """Catalog files in a local directory (``~/.cache/splashpy/contracts`` by default)."""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        """Use a directory: given, ``SPLASH_CONTRACTS_CACHE``, or the user cache directory."""
        self.path = Path(path) if path else default_cache_path()

    def read(self, name: str) -> bytes | None:
        """Read a catalog file, None when missing or unreadable."""
        try:
            return (self.path / name).read_bytes()
        except OSError:
            return None

    def write(self, name: str, raw: bytes) -> None:
        """Write a catalog file atomically (the directory is created when needed)."""
        self.path.mkdir(parents=True, exist_ok=True)
        temporary = self.path / f".{name}.tmp"
        temporary.write_bytes(raw)
        temporary.replace(self.path / name)


def default_cache_path() -> Path:
    """Default cache directory."""
    configured = os.environ.get(SplContracts.CACHE_ENV)
    if configured:
        return Path(configured)
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / SplContracts.CACHE_DIR
