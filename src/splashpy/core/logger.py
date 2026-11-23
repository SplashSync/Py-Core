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

"""Splash logger: messages collected during a request and returned to the Splash server.

One logger lives in each request context: messages never leak between requests.
"""

from __future__ import annotations

import logging
import traceback
from collections.abc import Mapping
from typing import Any, Final, Literal

ERROR: Final = "err"
"""Raw log key of errors."""

WARNING: Final = "war"
"""Raw log key of warnings."""

MESSAGE: Final = "msg"
"""Raw log key of messages."""

DEBUG: Final = "deb"
"""Raw log key of debug traces."""

_LEVELS: Final = {ERROR: logging.ERROR, WARNING: logging.WARNING, MESSAGE: logging.INFO, DEBUG: logging.DEBUG}
"""Mapping to Python logging levels."""


class Logger:
    """Collect error, warning, message and debug entries for the Splash server."""

    # ====================================================================#
    # Constructor
    # ====================================================================#

    def __init__(self, verbose: bool = False) -> None:
        """Create an empty logger; debug entries are only kept in verbose mode."""
        self.verbose = verbose
        self._entries: dict[str, list[str]] = {ERROR: [], WARNING: [], MESSAGE: [], DEBUG: []}

    # ====================================================================#
    # Logging
    # ====================================================================#

    def error(self, text: str) -> Literal[False]:
        """Add an error. Returns False, so ``return logger.error(...)`` reports a failure."""
        self._entries[ERROR].append(text)
        return False

    def warning(self, text: str) -> Literal[True]:
        """Add a warning."""
        self._entries[WARNING].append(text)
        return True

    def info(self, text: str) -> Literal[True]:
        """Add a message."""
        self._entries[MESSAGE].append(text)
        return True

    def debug(self, text: str) -> Literal[True]:
        """Add a debug trace (only kept in verbose mode)."""
        if self.verbose:
            self._entries[DEBUG].append(text)
        return True

    def exception(self, error: BaseException) -> Literal[False]:
        """Report an exception as an error, with its traceback as debug trace."""
        self.error(f"{type(error).__name__}: {error}")
        self.debug("".join(traceback.format_exception(type(error), error, error.__traceback__)))
        return False

    # ====================================================================#
    # Access & Exchange
    # ====================================================================#

    @property
    def has_errors(self) -> bool:
        """Check if at least one error was logged."""
        return bool(self._entries[ERROR])

    def entries(self, kind: str) -> list[str]:
        """Get a copy of the entries of one kind (``err``, ``war``, ``msg`` or ``deb``)."""
        return list(self._entries[kind])

    def export(self) -> dict[str, list[str]]:
        """Export entries in the Splash raw log format."""
        return {kind: list(entries) for kind, entries in self._entries.items()}

    def merge(self, raw: Any) -> None:
        """Merge a raw log received from the Splash server (decoded values: dicts, lists or strings)."""
        if not isinstance(raw, Mapping):
            return
        for kind, entries in self._entries.items():
            values = raw.get(kind)
            if isinstance(values, Mapping):
                values = list(values.values())
            if isinstance(values, list):
                entries.extend(str(value) for value in values if value)

    def clear(self) -> None:
        """Remove every entry."""
        for entries in self._entries.values():
            entries.clear()

    def flush(self, target: logging.Logger) -> None:
        """Write every entry to a Python logger, then clear."""
        for kind, entries in self._entries.items():
            for entry in entries:
                target.log(_LEVELS[kind], entry)
        self.clear()
