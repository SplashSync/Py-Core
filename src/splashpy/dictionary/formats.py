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

"""Formats of Splash field values: separators, dates and validation patterns."""

from __future__ import annotations

from typing import Final


class SplFormats:
    """Splash field values formats (mirror of Php-Core ``SPL_T_*`` constants)."""

    # ====================================================================#
    # Separators
    # ====================================================================#

    LIST_SPLIT: Final = "@"
    """Separator of list fields: ``field@list``."""

    ID_SPLIT: Final = "::"
    """Separator of object ids: ``id::Type``."""

    # ====================================================================#
    # Dates
    # ====================================================================#

    DATE: Final = "%Y-%m-%d"
    """Splash date format."""

    DATETIME: Final = "%Y-%m-%d %H:%M:%S"
    """Splash datetime format."""

    # ====================================================================#
    # Validation Patterns
    # ====================================================================#

    EMAIL: Final = r"[^@\s]+@[^@\s]+\.[^@\s.]+"
    """Email address: one ``@``, a domain with an extension."""

    URL_SCHEMES: Final = ("http", "https")
    """Accepted url schemes."""

    PHONE: Final = r"[+0-9. ()-]*[0-9][+0-9. ()-]*"
    """Phone number: Php-Core allowed characters, with at least one digit."""

    COUNTRY: Final = r"[A-Z]{2}"
    """Country: ISO 3166-1 alpha-2 code (``FR``)."""

    STATE: Final = r"([A-Z]{2}-)?[A-Z0-9]{1,3}"
    """State: ISO 3166-2 subdivision code, with or without its country (``CA``, ``US-CA``)."""

    LANG: Final = r"[a-z]{2}_[A-Z]{2}"
    """Language: ISO 639-1 language and ISO 3166-1 country (``fr_FR``)."""

    CURRENCY: Final = r"[A-Z]{3}"
    """Currency: ISO 4217 code (``EUR``)."""
