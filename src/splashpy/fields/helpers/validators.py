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


"""Basic field values validators.

Values received from Splash are kept as received: validators only tell if a value
respects the format of its field type, the connector decides what to do with an
invalid one (refuse, log or ignore it). Empty values are never valid.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit

from splashpy.dictionary import SplFormats
from splashpy.fields.helpers.dates import Dates


class Validators:
    """Check the format of basic field values (email, url, phone, country...)."""

    @staticmethod
    def is_email(value: Any) -> bool:
        """Check an email address."""
        return Validators._matches(SplFormats.EMAIL, value)

    @staticmethod
    def is_url(value: Any) -> bool:
        """Check an absolute http(s) url."""
        if not isinstance(value, str) or not value or any(char.isspace() for char in value):
            return False
        try:
            parts = urlsplit(value)
        except ValueError:
            return False
        return parts.scheme in SplFormats.URL_SCHEMES and bool(parts.hostname)

    @staticmethod
    def is_phone(value: Any) -> bool:
        """Check a phone number: digits, ``+``, dots, spaces, dashes and parentheses."""
        return Validators._matches(SplFormats.PHONE, value)

    @staticmethod
    def is_country(value: Any) -> bool:
        """Check an ISO 3166-1 alpha-2 country code (``FR``)."""
        return Validators._matches(SplFormats.COUNTRY, value)

    @staticmethod
    def is_state(value: Any) -> bool:
        """Check an ISO 3166-2 state code, with or without its country (``CA``, ``US-CA``)."""
        return Validators._matches(SplFormats.STATE, value)

    @staticmethod
    def is_lang(value: Any) -> bool:
        """Check a language code (``fr_FR``)."""
        return Validators._matches(SplFormats.LANG, value)

    @staticmethod
    def is_currency(value: Any) -> bool:
        """Check an ISO 4217 currency code (``EUR``)."""
        return Validators._matches(SplFormats.CURRENCY, value)

    @staticmethod
    def is_date(value: Any) -> bool:
        """Check a Splash date (``Y-m-d``)."""
        return isinstance(value, str) and len(value) == 10 and Dates.parse_date(value) is not None

    @staticmethod
    def is_datetime(value: Any) -> bool:
        """Check a Splash datetime (``Y-m-d H:i:s``)."""
        return isinstance(value, str) and len(value) == 19 and Dates.parse_datetime(value) is not None

    @staticmethod
    def _matches(pattern: str, value: Any) -> bool:
        """Check a whole string value against a pattern."""
        return isinstance(value, str) and re.fullmatch(pattern, value) is not None
