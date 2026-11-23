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


"""Contracts catalog: where Splash field templates & scopes are published (Php-Scopes)."""

from __future__ import annotations

from typing import Final


class SplContracts:
    """Php-Scopes catalog registry, files and format."""

    # ====================================================================#
    # Registry
    # ====================================================================#

    REGISTRY: Final = "https://gitlab.com/api/v4/projects/SplashTools%2Fscopes/packages/generic/catalog"
    """GitLab generic packages registry of the catalog (public): ``<REGISTRY>/<version>/<file>``."""

    VERSION: Final = "latest"
    """Registry version used by default (embedded snapshot and updates)."""

    TIMEOUT: Final = 30
    """Downloads timeout, in seconds."""

    # ====================================================================#
    # Files & Format
    # ====================================================================#

    INDEX: Final = "index.json"
    """Catalog index: version, commit and checksum of each file."""

    TEMPLATES: Final = "templates.json"
    """Field templates document."""

    SCOPES: Final = "scopes.json"
    """Scopes document."""

    FILES: Final = (TEMPLATES, SCOPES)
    """Documents used by splashpy (the index comes on top)."""

    FORMAT: Final = 1
    """Supported catalog format (major)."""

    DEFAULT_LANG: Final = "en_US"
    """Language always present in catalog texts."""

    # ====================================================================#
    # Cache
    # ====================================================================#

    CACHE_ENV: Final = "SPLASH_CONTRACTS_CACHE"
    """Environment variable overriding the cache directory."""

    CACHE_DIR: Final = "splashpy/contracts"
    """Cache directory, inside the user cache directory (``$XDG_CACHE_HOME`` or ``~/.cache``)."""
