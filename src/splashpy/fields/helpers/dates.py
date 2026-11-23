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


"""Dates and datetimes values."""

from __future__ import annotations

from datetime import date, datetime

from splashpy.dictionary import SplFormats


class Dates:
    """Splash dates and datetimes formats."""

    @staticmethod
    def to_date(value: date | None) -> str:
        """Format a date (empty string when None)."""
        return value.strftime(SplFormats.DATE) if value else ""

    @staticmethod
    def to_datetime(value: datetime | None) -> str:
        """Format a datetime (empty string when None)."""
        return value.strftime(SplFormats.DATETIME) if value else ""

    @staticmethod
    def parse_date(value: str | None) -> date | None:
        """Parse a Splash date, None when empty or invalid."""
        if not value:
            return None
        try:
            return datetime.strptime(value[:10], SplFormats.DATE).date()
        except ValueError:
            return None

    @staticmethod
    def parse_datetime(value: str | None) -> datetime | None:
        """Parse a Splash datetime (a date alone is accepted), None when empty or invalid."""
        if not value:
            return None
        for fmt in (SplFormats.DATETIME, SplFormats.DATE):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None
